from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession

from src.config import CSV_DATASETS, RAW_DATA_DIR, get_bronze_table_path, get_dataset_source_path
from src.spark_session import get_spark_session


def validate_input_files() -> None:
    missing_files = []
    for _, file_name in CSV_DATASETS.items():
        source_path = get_dataset_source_path(file_name)
        if not source_path.exists():
            missing_files.append(source_path)

    if missing_files:
        missing_lines = "\n".join(f"- {path}" for path in missing_files)
        raise FileNotFoundError(
            "Missing required Olist CSV files. Please verify raw data directory:\n"
            f"{RAW_DATA_DIR.resolve()}\n"
            f"{missing_lines}"
        )


def ingest_dataset(spark: SparkSession, dataset_name: str, file_name: str) -> None:
    source_path = get_dataset_source_path(file_name).resolve()
    source_uri = source_path.as_uri()
    target_path = get_bronze_table_path(dataset_name)

    print(f"[INGEST] Dataset: {dataset_name}")
    print(f"[INGEST] Source : {source_uri}")
    print(f"[INGEST] Target : {target_path}")

    dataframe = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(source_uri)
    )

    row_count = dataframe.count()

    (
        dataframe.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(target_path)
    )

    print(f"[DONE] Dataset: {dataset_name} | Rows: {row_count}")


def main() -> None:
    print("[START] Ingesting all Olist datasets into Bronze Delta layer.")
    print(f"[INFO] Raw data directory: {RAW_DATA_DIR.resolve()}")

    validate_input_files()

    spark = get_spark_session()

    try:
        for dataset_name, file_name in CSV_DATASETS.items():
            ingest_dataset(spark, dataset_name, file_name)
    finally:
        spark.stop()

    print("[SUCCESS] Bronze ingestion completed for all configured datasets.")


if __name__ == "__main__":
    main()
