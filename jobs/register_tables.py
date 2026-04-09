from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CSV_DATASETS, get_bronze_table_path
from src.spark_session import get_spark_session

def main() -> None:
    print("[START] Registering Bronze Delta tables to Hive Metastore...")
    spark = get_spark_session(app_name="olist-register-tables")

    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS default")

        for dataset_name in CSV_DATASETS.keys():
            table_name = f"olist_{dataset_name}"
            s3_path = get_bronze_table_path(dataset_name)
            
            print(f"[REGISTER] Table: default.{table_name} -> {s3_path}")
            spark.sql(
                f"CREATE TABLE IF NOT EXISTS default.{table_name} "
                f"USING DELTA LOCATION '{s3_path}'"
            )

        print("-" * 50)
        print("[INFO] Showing all tables in 'default' database:")
        spark.sql("SHOW TABLES IN default").show(truncate=False)
        print("-" * 50)
        print("[SUCCESS] All Bronze Delta tables have been successfully registered.")

    finally:
        spark.stop()

if __name__ == "__main__":
    main()
