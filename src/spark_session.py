from __future__ import annotations

import os

from pyspark.sql import SparkSession

from src.config import (
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    SPARK_JARS_PACKAGES,
    SPARK_MASTER,
)


def get_spark_session(app_name: str = "olist-bronze-ingestion") -> SparkSession:
    builder = SparkSession.builder.appName(app_name).master(SPARK_MASTER)

    if "--packages" not in os.getenv("PYSPARK_SUBMIT_ARGS", ""):
        builder = builder.config("spark.jars.packages", SPARK_JARS_PACKAGES)

    builder = (
        builder.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.catalogImplementation", "hive")
        .config("spark.sql.warehouse.dir", "s3a://bronze/warehouse")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        # Hive Metastore JDBC Configuration (PostgreSQL)
        .config(
            "spark.hadoop.javax.jdo.option.ConnectionURL",
            f"jdbc:postgresql://{os.getenv('POSTGRES_HOST', 'postgres')}:5432/{os.getenv('POSTGRES_DB', 'metastore')}",
        )
        .config("spark.hadoop.javax.jdo.option.ConnectionDriverName", "org.postgresql.Driver")
        .config(
            "spark.hadoop.javax.jdo.option.ConnectionUserName",
            os.getenv("POSTGRES_USER", "metastore"),
        )
        .config(
            "spark.hadoop.javax.jdo.option.ConnectionPassword",
            os.getenv("POSTGRES_PASSWORD", "metastore123"),
        )
        # ER-01: autoCreateAll=false — schema đã được tạo sẵn bởi sql script
        # ER-01: verification=false  — bỏ qua Hive version check
        .config("spark.hadoop.datanucleus.schema.autoCreateAll", "false")
        .config("spark.hadoop.hive.metastore.schema.verification", "false")
        # Classpath for Hive Metastore JDBC Driver
        .config("spark.driver.extraClassPath", "/opt/airflow/jars/postgresql-42.7.4.jar")
        .config("spark.executor.extraClassPath", "/opt/airflow/jars/postgresql-42.7.4.jar")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
