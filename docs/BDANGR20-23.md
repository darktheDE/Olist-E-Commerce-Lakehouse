BDANGR20-23
[Issue 3] Cấu hình Hive Metastore (Data Catalog)
* **Mô tả:** Thiết lập Hive Metastore để quản lý metadata (bảng, schema) của các Delta Tables, giúp các thành viên có thể dùng spark.sql("SELECT * FROM ...") thay vì đọc đường dẫn vật lý.

* **Các bước triển khai (Step-by-step):**

  1. Bổ sung cấu hình Hive vào file spark-defaults.conf (hoặc ngay trong lúc tạo SparkSession). Bật cờ spark.sql.catalogImplementation=hive.

  2. Viết 1 script nhỏ register_[tables.py](http://tables.py) để khai báo các bảng ở bucket Bronze vào Catalog.

  3. _Ví dụ code:_ spark.sql("CREATE TABLE IF NOT EXISTS default.orders USING DELTA LOCATION 's3a://bronze/olist_orders'").

  4. Test thử bằng cách chạy lệnh SQL SHOW TABLES;.

### Log Triển Khai Step-by-Step

- **[Khắc phục lỗi JDBC Driver]**: Spark bị lỗi `java.sql.SQLException: No suitable driver found` do cấu hình `spark-defaults.conf` không đủ đảm nhiệm việc tải gói lúc runtime cho Hive Catalog. Đã giải quyết bằng cách thủ công load file `postgresql-42.7.4.jar` vào `/usr/local/spark/jars` của container `olist-pyspark-notebook` tự động nếu chưa có, và cấu hình `--driver-class-path /usr/local/spark/jars/postgresql-42.7.4.jar` khi submit jobs.
- **[Cấu hình Spark - DataNucleus Deadlock]**: Gặp sự cố DataNucleus cố tính tạo khóa và tranh chấp table `TBL_PRIVS` ở database Postgres dẫn đến timeout lúc đăng ký Table. Cách xử lý là chạy script chuẩn của Hive (`hive-schema-2.3.0.postgres.sql`) trực tiếp vào Postgres để build Schema trước, thay vì dựa vào auto-create của DataNucleus. Sau đó đặt `spark.hadoop.datanucleus.schema.autoCreateAll=false` và `spark.hadoop.hive.metastore.schema.verification=true`.
- **[Cấu hình Spark - Warehouse Permission]**: Để tránh lỗi `Operation not permitted` khi `spark-warehouse` bị share qua Docker volumes cho người dùng `jovyan`, cấu hình `spark.sql.warehouse.dir` đã được định tuyến trực tiếp về `s3a://bronze/warehouse` để lưu file Metadata và virtual tables thẳng trên MinIO trong `src/spark_session.py`. 
- **[Đăng ký Tables và Validate]**: 
  - Tạo logic ở `jobs/register_tables.py` gọi method `CREATE TABLE IF NOT EXISTS ... USING DELTA LOCATION 's3a://...'` liên tục chạy trơn tru qua `io.delta:delta-spark` mà không gặp chướng ngại nào.
  - Viết script `jobs/check_tables.py` gọi method `spark.sql("SHOW TABLES IN default")` và `spark.sql("SELECT COUNT(*) FROM default.olist_orders")`. Bảng hiện rõ trong Database Catalog của Hive (`olist_category_name_translation`, `olist_orders`, v.v..) với bản ghi đạt khoảng `99,441` rows, trả lời trực tiếp từ Metadata của Hive. Cấu hình hoàn tất!

### Định Nghĩa Hoàn Thành Task (Definition of Done)
1. **Không còn lỗi kết nối JDBC Driver**: Spark có thể nạp thành công PostgreSQL JDBC Driver sớm nhất trong quá trình khởi tạo SparkSession và giao tiếp với Hive Metastore (`olist-postgres`).
2. **Schema Metadata Khởi Tạo Thành Công**: Các system config schemas của Hive (khoảng 45+ tables như `TBLS`, `DBS`, v.v..) đã được ghi nhận trong database Hive Postgres.
3. **Data Xung Đột Phân Quyền (Permission) Xử Lý Triệt Để**: `spark-warehouse` giải quyết bằng cách mount trỏ thẳng S3A vào zone Data Lake (`s3a://bronze/warehouse` trên MinIO).
4. **Khả Năng Truy Vấn Metadata Delta Tables**: Delta tables tại đường dẫn `s3a://bronze/...` được ánh xạ thành các bảng logical trong Spark Catalog SQL. Người dùng có thể sử dụng `spark.sql("SHOW TABLES")` và `spark.sql("SELECT * FROM table_name")` tự nhiên.

### Hướng Dẫn Kiểm Tra Task (Step-by-step Check)
1. Bật toàn bộ architecture Docker bằng lệnh `docker-compose up -d`.
2. Theo lý thuyết, dữ liệu từ hệ thống Bronze đã được Ingest ở Task số 2.
3. Gọi container thực hiện script bằng câu lệnh:
   ```bash
   docker exec olist-pyspark-notebook spark-submit --driver-class-path /usr/local/spark/jars/postgresql-42.7.4.jar /home/jovyan/work/jobs/check_tables.py
   ```
4. Kiểm tra output Terminal xem có xuất hiện thông tin:
   - Các cảnh báo `WARN HiveExternalCatalog` (đây là cảnh báo an toàn từ Spark SQL thông báo cơ chế chuyển đổi SerDe giữa format đặc tả Spark's Delta so với Hive cũ).
   - Bảng in ra từ CLI hiển thị log `[INFO] SHOW DATABASES` gồm namespace `default`.
   - Danh sách chứa 9 Table có tiền tố **`olist_`** (có cột `isTemporary=false`).
   - Kết quả xuất ra từ test lệnh select truy vấn `default.olist_orders` đổ về đúng count bằng `99441`.