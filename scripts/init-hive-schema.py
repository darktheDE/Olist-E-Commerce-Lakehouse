#!/usr/bin/env python3
"""
init-hive-schema.py
-------------------
Khởi tạo Hive Metastore schema trên PostgreSQL backend.
Script này chạy DUY NHẤT 1 LẦN khi lần đầu `docker compose up`
(hoặc sau khi xóa volume postgres_data).

Cơ chế:
  - DataNucleus với datanucleus.schema.autoCreateAll=true sẽ tự tạo
    toàn bộ bảng Hive (DBS, SDS, TBLS, VERSION, ...) nếu chưa tồn tại.
  - Nếu schema đã tồn tại, DataNucleus bỏ qua (idempotent - an toàn
    khi chạy lại).
  - Sau khi script này exit 0, các service khác (spark-thrift-server,
    airflow-*) mới được phép start (via depends_on condition).
"""
import os
import sys
import traceback

print("[HIVE-INIT] ========================================", flush=True)
print("[HIVE-INIT]  Hive Metastore Schema Initialization  ", flush=True)
print("[HIVE-INIT] ========================================", flush=True)

# --- Import PySpark -----------------------------------------------------------
try:
    from pyspark.sql import SparkSession
except ImportError as exc:
    print(f"[HIVE-INIT] FATAL: pyspark not importable: {exc}", flush=True)
    print("[HIVE-INIT] Check PYTHONPATH in the container.", flush=True)
    sys.exit(1)

# --- Config từ biến môi trường ------------------------------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB   = os.getenv("POSTGRES_DB", "metastore")
POSTGRES_USER = os.getenv("POSTGRES_USER", "metastore")
POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "metastore123")

JDBC_URL = f"jdbc:postgresql://{POSTGRES_HOST}:5432/{POSTGRES_DB}"
JDBC_JAR = "/opt/spark/extra-jars/postgresql-42.7.4.jar"

print(f"[HIVE-INIT] JDBC URL  : {JDBC_URL}", flush=True)
print(f"[HIVE-INIT] JDBC JAR  : {JDBC_JAR}", flush=True)
print(f"[HIVE-INIT] DB User   : {POSTGRES_USER}", flush=True)

# --- Khởi tạo SparkSession với autoCreateAll=true ----------------------------
try:
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("hive-metastore-init")
        # JDBC driver cho PostgreSQL
        .config("spark.driver.extraClassPath", JDBC_JAR)
        # Hive catalog
        .config("spark.sql.catalogImplementation", "hive")
        # Warehouse dir tạm — không liên quan đến MinIO
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-init")
        # Hive Metastore JDBC
        .config("spark.hadoop.javax.jdo.option.ConnectionURL", JDBC_URL)
        .config("spark.hadoop.javax.jdo.option.ConnectionDriverName",
                "org.postgresql.Driver")
        .config("spark.hadoop.javax.jdo.option.ConnectionUserName", POSTGRES_USER)
        .config("spark.hadoop.javax.jdo.option.ConnectionPassword", POSTGRES_PASS)
        # DataNucleus: TỰ TẠO SCHEMA — chỉ dùng cho init này
        .config("spark.hadoop.datanucleus.schema.autoCreateAll", "true")
        .config("spark.hadoop.datanucleus.fixedDatastore", "false")
        .config("spark.hadoop.datanucleus.autoStartMechanismMode", "checked")
        # Tắt version verification để tránh lỗi khi schema mới được tạo
        .config("spark.hadoop.hive.metastore.schema.verification", "false")
        .enableHiveSupport()
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    print("[HIVE-INIT] SparkSession created. Verifying schema...", flush=True)
    dbs = spark.sql("SHOW DATABASES").collect()
    db_names = [row[0] for row in dbs]
    print(f"[HIVE-INIT] Databases in metastore: {db_names}", flush=True)

    spark.stop()
    print("[HIVE-INIT] ✓ SUCCESS: Hive Metastore schema ready.", flush=True)
    sys.exit(0)

except Exception as exc:
    print(f"[HIVE-INIT] ✗ FAILED: {exc}", flush=True)
    traceback.print_exc()
    sys.exit(1)
