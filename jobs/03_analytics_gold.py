from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql.functions import (
    col,
    countDistinct,
    datediff,
    expr,
    max as _max,
    ntile,
    sum as _sum,
    when,
    concat,
    lit
)
from pyspark.sql.window import Window
from src.config import get_gold_table_path
from src.spark_session import get_spark_session


def main() -> None:
    print("[START] Building Gold Layer (RFM Customer Segmentation)...")
    spark = get_spark_session(app_name="olist-gold-rfm-analysis")

    try:
        # 1. Đọc dữ liệu từ Silver Layer (Hive Table)
        # Lưu ý: Nếu bảng chưa tồn tại trong Hive, ta có thể đăng ký trực tiếp từ S3
        # Ở đây ta giả định silver_sales đã sẵn sàng
        print("[INFO] Loading silver_sales table...")
        try:
            silver_sales = spark.table("default.silver_sales")
        except Exception as e:
            print(f"[WARN] Table default.silver_sales not found in Hive. Trying to register from S3...")
            from src.config import get_silver_table_path
            silver_path = get_silver_table_path("denormalized_sales")
            spark.sql(f"CREATE TABLE IF NOT EXISTS default.silver_sales USING DELTA LOCATION '{silver_path}'")
            silver_sales = spark.table("default.silver_sales")

        # 2. Aggregation: Tính metrics cơ bản cho từng khách hàng duy nhất
        print("[INFO] Calculating basic R, F, M metrics per unique customer...")
        # Lấy ngày mua hàng cuối cùng trong toàn bộ tập dữ liệu để làm mốc tham chiếu
        # Vì dữ liệu Olist mang tính lịch sử, ta không dùng current_date() của hệ thống.
        max_date_row = silver_sales.select(_max("order_purchase_timestamp")).collect()[0]
        max_date = max_date_row[0]
        print(f"[INFO] Max purchase date in dataset: {max_date}")

        # Ngày tham chiếu = max_date + 1 day
        reference_date_expr = f"CAST('{max_date}' AS TIMESTAMP) + INTERVAL 1 DAY"
        
        rfm_base = (
            silver_sales.groupBy("customer_unique_id")
            .agg(
                _max("order_purchase_timestamp").alias("last_purchase_date"),
                countDistinct("order_id").alias("frequency"),
                _sum(col("price") + col("freight_value")).alias("monetary")
            )
            .withColumn("recency", datediff(expr(reference_date_expr), col("last_purchase_date")))
        )

        # 3. Scoring: Chia các metrics thành 4 quartile (ntile 4)
        print("[INFO] Assigning scores (1-4) using ntile window functions...")
        
        window_r = Window.orderBy(col("recency").desc()) # Ngày gần nhất (recency nhỏ) ở cuối -> group 4
        window_f = Window.orderBy(col("frequency").asc()) # Freq cao ở cuối -> group 4
        window_m = Window.orderBy(col("monetary").asc())  # Spend cao ở cuối -> group 4

        rfm_scores = (
            rfm_base
            .withColumn("r_score", ntile(4).over(window_r))
            .withColumn("f_score", ntile(4).over(window_f))
            .withColumn("m_score", ntile(4).over(window_m))
        )

        # 4. RFM Score & Segmentation
        print("[INFO] Creating RFM segments and score strings...")
        rfm_segments = rfm_scores.withColumn(
            "rfm_score_string", 
            concat(col("r_score").cast("string"), col("f_score").cast("string"), col("m_score").cast("string"))
        ).withColumn(
            "rfm_segment",
            when(col("rfm_score_string") == "444", "Champions/VIP")
            .when(col("r_score") == 4, "Recent Customers")
            .when(col("f_score") == 4, "Loyal Customers")
            .when(col("m_score") == 4, "Big Spenders")
            .when(col("r_score") <= 1, "Lost Customers")
            .when(col("r_score") <= 2, "At Risk")
            .otherwise("General Customers")
        )

        # 5. Lưu kết quả ra Gold Layer (S3 + Hive)
        target_path = get_gold_table_path("rfm_segments")
        print(f"[INFO] Saving results to {target_path} partitioned by rfm_segment...")

        (
            rfm_segments.write.format("delta")
            .mode("overwrite")
            .partitionBy("rfm_segment")
            .option("overwriteSchema", "true")
            .save(target_path)
        )

        # Đăng ký vào Hive Metastore
        table_name = "default.gold_rfm_segments"
        print(f"[REGISTER] Registering table {table_name} into Hive...")
        spark.sql(
            f"CREATE TABLE IF NOT EXISTS {table_name} "
            f"USING DELTA LOCATION '{target_path}'"
        )

        print("-" * 50)
        print("[INFO] Distribution of segments:")
        spark.sql(f"SELECT rfm_segment, COUNT(*) as count, ROUND(AVG(monetary), 2) as avg_monetary FROM {table_name} GROUP BY 1 ORDER BY 2 DESC").show()
        print("-" * 50)

        print("[SUCCESS] Gold Layer - RFM Analysis completed successfully.")

    except Exception as e:
        print(f"[ERROR] Task failed: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
