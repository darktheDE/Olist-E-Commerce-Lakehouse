[Issue 6] Thiết kế Airflow DAG (Orchestration)
* **Mô tả:** Thay vì chạy script bằng tay, cấu hình Airflow để chạy tự động theo luồng Bronze -> Silver -> Gold.

* **Các bước triển khai (Step-by-step):**

  1. Cài đặt Airflow (local hoặc thêm vào file docker-compose).

  2. Tạo file olist_lakehouse_dag.py trong thư mục dags.

  3. Sử dụng BashOperator hoặc SparkSubmitOperator để gọi tuần tự 3 file script: ingest_bronze.py >> process_silver.py >> analytics_gold.py.

  4. Bật Airflow Web UI, kích hoạt DAG và chụp lại biểu đồ Gantt/Graph để đưa vào báo cáo.

---
## Nhật ký triển khai (Execution Log)

### Bước 1: Chuẩn bị hạ tầng (Infrastructure)
- Tạo **Dockerfile.airflow** kế thừa `apache/airflow:2.8.1`, cài đặt thêm **JRE** và **pyspark**, **delta-spark** để chạy Spark job local.
- Tạo script **init-airflow-db.sql** trong thư mục `scripts/` để tự động khởi tạo database `airflow` trong Postgres container.
- Cấu hình lại **docker-compose.yml**:
    - Thêm các service: `airflow-webserver`, `airflow-scheduler`, `airflow-init`.
    - Map volume cho `dags/`, `jobs/`, `src/`, `data/`, `conf/`, `logs/`.
    - Thêm script init SQL vào volume của service `postgres`.
- Cập nhật file **.env** với các biến môi trường cần thiết (`AIRFLOW_UID`, `AIRFLOW_GID`, ...).

### Bước 2: Phát triển DAG
- Tạo file **dags/olist_lakehouse_dag.py**.
- Sử dụng **BashOperator** để gọi tuần tự 5 script xử lý:
    1. `ingest_bronze`: Chạy `jobs/01_ingest_bronze.py` (Draft CSV -> Delta).
    2. `register_tables`: Chạy `jobs/register_tables.py` (Đăng ký Delta vào Hive).
    3. `check_tables`: Chạy `jobs/check_tables.py` (Kiểm tra Catalog).
    4. `process_silver`: Chạy `jobs/02_process_silver.py` (Bronze -> Silver).
    5. `analytics_gold`: Chạy `jobs/03_analytics_gold.py` (Silver -> Gold).
- Thiết lập dependencies: `ingest_bronze >> register_tables >> check_tables >> process_silver >> analytics_gold`.

### Bước 3: Tài liệu hóa (Documentation)
- Cập nhật file **DEVELOPMENT.md**, bổ sung mục hướng dẫn vận hành Airflow, tài khoản đăng nhập (`admin` / `admin`) và cách trigger DAG.

### Bước 4: Sửa lỗi hạ tầng (Troubleshooting & Bug Fixes)
Trong quá trình chạy DAG, đã phát sinh và giải quyết các vấn đề quan trọng sau:
1. **Lỗi `[TABLE_OR_VIEW_NOT_FOUND]` ở task Silver:**
   - *Nguyên nhân:* Xử lý Silver cố gắng gọi bảng qua `spark.table()` nhưng bảng chưa được đăng ký vào Hive Metastore.
   - *Khắc phục:* Bổ sung script `register_tables.py` và `check_tables.py` vào luồng DAG, chạy ngay sau khi ingest xong.
2. **Lỗi truy vấn Metastore không đồng bộ:**
   - *Nguyên nhân:* Các file jobs dưới quyền Airflow đang tự dùng file Derby nội bộ thay vì dùng chung PostgreSQL của dự án do thiếu config.
   - *Khắc phục:* Cập nhật file `src/spark_session.py` và `src/config.py` bổ sung cầu nối JDBC tới hostname `postgres` chạy qua port 5432.
3. **Lỗi `No suitable driver found` khi Airflow chạy PySpark:**
   - *Nguyên nhân:* Option `--packages` tải driver PostgreSQL tại lúc Runtime sau khi Spark Session (Hive instance) đã được nạp nên không tìm thấy driver.
   - *Khắc phục:* (Giống với xử lý ở Notebook ở Task 23), đã tạo thư mục `./jars` ở máy host và tải trực tiếp file `postgresql-42.7.4.jar`. Phân quyền `volume` file này vào container của Airflow và nạp cờ biên dịch `PYSPARK_SUBMIT_ARGS` trong file `docker-compose.yml` (`--jars ... --driver-class-path ...`) giúp PySpark của Airflow nạp Driver ngay từ lúc khởi động.

---

## Định nghĩa hoàn thành (Definition of Done - DoD)
- [x] Airflow khởi động thành công và kết nối được với metadata database (Postgres).
- [x] DAG `olist_lakehouse_pipeline` hiển thị chính xác trên Web UI với đầy đủ 5 task.
- [x] Cấu hình Docker Compose không gặp lỗi logic hoặc cú pháp.
- [x] File `DEVELOPMENT.md` phản ánh đúng cách sử dụng Airflow trong dự án.

---

## Cách kiểm tra thủ công (Manual Verification Guide)
1. **Khởi động:** Chạy `docker-compose up -d`.
2. **Truy cập:** Mở trình duyệt tại `http://localhost:8080`. Đăng nhập bằng `admin` / `admin`.
3. **Kích hoạt:** Tìm DAG `olist_lakehouse_pipeline`, bật (unpause) và nhấn nút **Trigger DAG**.
4. **Kiểm tra luồng:** Vào mục **Graph View** để xem trạng thái 5 task. Đảm bảo tất cả các task chuyển sang màu xanh lá cây (Success).
5. **Kiểm tra Log:** Click vào từng task -> **Logs** để xác nhận các bản ghi Python/Spark đã chạy đúng logic Lakehouse. Đặc biệt xem task `check_tables` để xác nhận các bảng đã có trong Hive.
6. **Kiểm tra dữ liệu:** Truy cập MinIO hoặc dùng script check tables để xác nhận dữ liệu đã được ghi vào các bucket Bronze, Silver, Gold.
