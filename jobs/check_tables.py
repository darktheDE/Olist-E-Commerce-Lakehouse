import os
import sys

# Thêm src vào sys.path để import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.spark_session import get_spark_session

def main():
    spark = get_spark_session("Check Hive Tables")
    print("\n[INFO] SHOW DATABASES:")
    spark.sql("SHOW DATABASES").show(truncate=False)
    
    print("\n[INFO] SHOW TABLES IN default:")
    spark.sql("SHOW TABLES IN default").show(truncate=False)

    print("\n[INFO] ROW COUNT in default.olist_orders:")
    spark.sql("SELECT COUNT(*) as order_count FROM default.olist_orders").show(truncate=False)

if __name__ == "__main__":
    main()
