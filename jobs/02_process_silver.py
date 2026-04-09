from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql.functions import col, coalesce, to_timestamp
from src.config import get_silver_table_path
from src.spark_session import get_spark_session


def main() -> None:
    print("[START] Building Silver Layer (Data Cleansing & Denormalization)...")
    spark = get_spark_session(app_name="olist-silver-processing")

    try:
        # 1. Đọc dữ liệu từ Hive Catalog
        print("[INFO] Reading Bronze tables from Hive Catalog...")
        orders = spark.table("default.olist_orders")
        customers = spark.table("default.olist_customers")
        order_items = spark.table("default.olist_order_items")
        products = spark.table("default.olist_products")

        # 2. Làm sạch (Cleansing)
        print("[INFO] Cleansing orders data...")
        # Lọc bỏ các đơn hàng đã bị hủy
        orders = orders.filter(col("order_status") != "canceled")
        
        # Xử lý null ở cột order_delivered_customer_date bằng order_estimated_delivery_date
        orders = orders.withColumn(
            "order_delivered_customer_date",
            coalesce(col("order_delivered_customer_date"), col("order_estimated_delivery_date"))
        )

        # 3. Chuẩn hóa (Standardization)
        print("[INFO] Casting datetime columns to Timestamp...")
        time_cols = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
        for c in time_cols:
            orders = orders.withColumn(c, to_timestamp(col(c)))

        # 4. Join bảng
        print("[INFO] Denormalizing data by joining tables...")
        # orders -> customers (1-1)
        # orders -> order_items (1-N)
        # order_items -> products (N-1)
        denormalized_sales = (
            orders
            .join(customers, "customer_id", "left")
            .join(order_items, "order_id", "left")
            .join(products, "product_id", "left")
        )

        row_count = denormalized_sales.count()
        print(f"[INFO] Total denormalized records joined: {row_count}")

        # 5. Lưu vào S3 (MinIO) dưới định dạng Delta
        target_path = get_silver_table_path("denormalized_sales")
        print(f"[INFO] Saving silver layer data to {target_path} ...")
        
        (
            denormalized_sales.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(target_path)
        )

        # 6. Đăng ký bảng vào Hive Catalog
        table_name = "default.silver_sales"
        print(f"[REGISTER] Registering table {table_name} into Hive Metastore...")
        spark.sql(
            f"CREATE TABLE IF NOT EXISTS {table_name} "
            f"USING DELTA LOCATION '{target_path}'"
        )

        print("[SUCCESS] Silver Layer processing completed successfully.")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
