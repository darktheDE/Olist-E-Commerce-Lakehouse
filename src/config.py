from __future__ import annotations

import os
from pathlib import Path


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"http://{endpoint}"


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = Path(
    os.getenv("OLIST_RAW_DATA_DIR", str(PROJECT_ROOT / "data" / "raw" / "olist"))
)

MINIO_ENDPOINT = _normalize_endpoint(os.getenv("MINIO_ENDPOINT", "localhost:9000"))
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BRONZE_BUCKET = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
SILVER_BUCKET = os.getenv("MINIO_BUCKET_SILVER", "silver")
GOLD_BUCKET = os.getenv("MINIO_BUCKET_GOLD", "gold")

# PostgreSQL (Hive metastore backend)
POSTGRES_DB = os.getenv("POSTGRES_DB", "metastore")
POSTGRES_USER = os.getenv("POSTGRES_USER", "metastore")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "metastore123")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")

SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")

DELTA_SPARK_PACKAGE_VERSION = os.getenv("DELTA_SPARK_PACKAGE_VERSION", "3.2.0")
HADOOP_AWS_PACKAGE_VERSION = os.getenv("HADOOP_AWS_PACKAGE_VERSION", "3.3.4")
AWS_JAVA_SDK_BUNDLE_VERSION = os.getenv("AWS_JAVA_SDK_BUNDLE_VERSION", "1.12.262")

SPARK_JARS_PACKAGES = os.getenv(
    "SPARK_JARS_PACKAGES",
    ",".join(
        [
            f"io.delta:delta-spark_2.12:{DELTA_SPARK_PACKAGE_VERSION}",
            f"org.apache.hadoop:hadoop-aws:{HADOOP_AWS_PACKAGE_VERSION}",
            f"com.amazonaws:aws-java-sdk-bundle:{AWS_JAVA_SDK_BUNDLE_VERSION}",
            "org.postgresql:postgresql:42.7.4",
        ]
    ),
)

CSV_DATASETS: dict[str, str] = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "category_name_translation": "product_category_name_translation.csv",
}


def get_dataset_source_path(file_name: str) -> Path:
    return RAW_DATA_DIR / file_name


def get_bronze_table_path(dataset_name: str) -> str:
    return f"s3a://{BRONZE_BUCKET}/olist_{dataset_name}"


def get_silver_table_path(dataset_name: str) -> str:
    return f"s3a://{SILVER_BUCKET}/{dataset_name}"


def get_gold_table_path(table_name: str) -> str:
    return f"s3a://{GOLD_BUCKET}/{table_name}"
