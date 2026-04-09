Trước khi triển khai task, bạn hãy:
- Đọc kỹ tài liệu dự án, những task đã triển khai trước đó để lấy ngữ cảnh thực hiện task này. Đọc kỹ file README.md, .env, .env.example, các file conf, ... để lấy ngữ cảnh triển khai.
- Bạn cần search trong .agent/skill, chọn những skill phù hợp với task để lấy ngữ cảnh thực hiện task này.
- Kiểm tra xem task này có hợp lý với dự án hay không, có phải best implementation không, nếu không thì đề xuất thay đổi, bổ sung. Nội dung của task được gen bằng AI Studio, nội dung cùng chung ngữ cảnh phát triển nhưng có thể không tối ưu.
- Đề xuất thay đổi nếu cần thiết.
- Cần rà soát xem có những lỗi nào, rà soát những vấn đề có thể sảy ra, lên kế hoạch trước ở phần lên plan.
- Mọi hoạt động triển khai task cần viết ngắn gọn nhưng đầy đủ, súc tích, step by step bằng tiếng việt vào chính doc này - <Mã-task>.md
- Sau khi kiểm tra, chuẩn bị mọi thứ cho task, hãy lên kế hoạch thực hiện task, chờ tôi duyệt, không triển khai ngay.
- Bạn có toàn quyền truy cập vào các file như file conf, file .env, .env.example, các file gitignore, ... để phục vụ cho việc triển khai task. Bạn có thể tự do chỉnh sửa, bổ sung, thay đổi các file này nếu cần thiết. Đảm bảo các file hợp lý, sync với nhau.

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
