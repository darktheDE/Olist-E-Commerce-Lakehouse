# [Issue 7] Trực quan hóa dữ liệu (Apache Superset & Spark Thrift Server)

*   **Mô tả:** Thiết lập hạ tầng BI, kết nối công cụ Apache Superset vào lớp Gold layer thông qua Spark Thrift Server để phục vụ phân tích dữ liệu.
*   **Trạng thái:** ✅ ĐÃ HOÀN THÀNH - Sẵn sàng cho Dashboarding.

---

## 1. Nhật ký triển khai chi tiết (Detailed Execution Log)

### 1.1. Hạ tầng hóa (Infrastructure)
1.  **Cấu hình môi trường:**
    - Cập nhật `.env` hỗ trợ Superset: `SUPERSET_SECRET_KEY`, `SUPERSET_ADMIN`, `SUPERSET_PASSWORD`.
2.  **Mở rộng Docker Compose:**
    - Khai báo service `spark-thrift-server` dựa trên image `apache/spark:3.5.0`.
    - Khai báo service `superset` sử dụng image `apache/superset:latest`.
    - Thiết lập mạng nội bộ `lakehouse-network` để các service giao tiếp qua container name.

### 1.2. Khởi tạo Superset
1.  **Scripting:** Viết script `scripts/setup-superset.sh` để tự động hóa các bước:
    - `superset db upgrade`: Nâng cấp database metadata nội bộ.
    - `superset fab create-admin`: Tạo tài khoản quản trị từ biến môi trường.
    - `superset init`: Cấu hình phân quyền mặc định.
2.  **Automation:** Viết script `scripts/register_database.py` sử dụng Superset API để đăng ký tự động database JDBC connection, tránh việc người dùng phải nhập tay thông tin phức tạp.

---

## 2. Deep Dive: Giải quyết các lỗi nghiêm trọng (Troubleshooting)

Trong quá trình triển khai, hệ thống gặp phải 3 lỗi "nút thắt" ngăn cản kết nối. Dưới đây là phân tích kỹ thuật và giải pháp:

### 2.1. Lỗi Driver SQLAlchemy Hive
- **Triệu chứng:** `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:hive`.
- **Nguyên nhân:** Image Superset mặc định không có thư viện `pyhive` và các dependency C++ (`libsasl2-dev`). Khi cài bằng `pip`, do Superset chạy trong môi trường ảo nội bộ (`venv`), lệnh `pip install` thông thường sẽ cài vào thư mục system thay vì venv.
- **Giải pháp:** 
    - Cài đặt `g++` và `libsasl2-dev` thông qua `apt-get` trong command khởi chạy.
    - Sử dụng `pip install --target /app/.venv/lib/python3.10/site-packages pyhive thrift sasl` để ép driver vào đúng môi trường active của Superset.

### 2.2. Lỗi Delta Catalog trên ClassPath
- **Triệu chứng:** `java.lang.NoClassDefFoundError: org/apache/spark/sql/delta/catalog/DeltaCatalog`.
- **Nguyên nhân:** Spark Thrift Server yêu cầu các lớp Catalog như `DeltaCatalog` phải tồn tại trong **System ClassLoader** ngay khi khởi động JVM. Việc sử dụng tham số `--packages` chỉ nạp thư viện vào *Application ClassLoader*, dẫn đến việc Catalog Management của Spark không tìm thấy lớp Delta.
- **Giải pháp:** 
    - Trích xuất thủ công các file JAR cần thiết (Delta Spark, S3 SDK, ANTLR) từ Ivy cache ra thư mục `./jars` vật lý.
    - Cấu hình `docker-compose` sử dụng `--driver-class-path "/opt/spark/extra-jars/*"` và `--jars "/opt/spark/extra-jars/*"`. 
    - Điều này đảm bảo thư viện có mặt ở mức hệ thống cao nhất.

### 2.3. Lỗi xác thực AWS (NoAwsCredentialsException)
- **Triệu chứng:** `org.apache.hadoop.fs.s3a.auth.NoAwsCredentialsException: No AWS credentials in the Hadoop configuration`.
- **Nguyên nhân:** Mặc dù Spark đã nhận diện được đường dẫn `s3a://`, nhưng Spark Thrift Server không tự động kế thừa bộ Key từ environment của các service khác khi tương tác với MinIO.
- **Giải pháp:** 
    - Bổ sung cấu hình cứng (hoặc qua biến môi trường) vào `conf/spark-defaults.conf`:
        - `spark.hadoop.fs.s3a.access.key`: `minioadmin`
        - `spark.hadoop.fs.s3a.secret.key`: `minioadmin`
    - Cấu hình này giúp S3A FileSystem của Hadoop có đủ thông tin để "nói chuyện" with MinIO.

### 2.4. Lỗi Push Git do File JAR quá nặng (>100MB)
- **Triệu chứng:** Kết quả `git push` bị từ chối bởi GitHub với lỗi: `this exceeds GitHub's file size limit of 100.00 MB`. Cụ thể là file `aws-java-sdk-bundle-1.12.262.jar` nặng 267MB.
- **Nguyên nhân:** Do yêu cầu nạp thư viện vào *System ClassLoader* (để xử lý lỗi 2.2), các file JAR đã được lưu thủ công vào thư mục `jars/` và vô tình được commit vào lịch sử dự án.
- **Giải pháp:** 
    - Thực hiện `git reset --soft` để hủy commit lỗi và đưa các file trở lại trạng thái staged.
    - Cập nhật `.gitignore` để loại trừ vĩnh viễn thư mục `jars/` và tất cả file `*.jar`.
    - Viết script `scripts/fetch-jars.sh` để tự động hóa việc tải JAR từ Maven Central về local khi setup dự án, thay vì lưu trữ chúng trực tiếp trong Git. 
    - Duy trì việc mount volume trong `docker-compose.yml` để cung cấp JAR cho container mà không cần đưa JAR vào repository.

---

## 3. Hướng dẫn tạo Dashboard trên Superset (User Guide)

Hệ thống đã được cấu hình sẵn Database Connection mang tên **"Olist Lakehouse (Spark)"**.

### Quy trình các bước:
1.  **Truy cập:** `http://localhost:8088` (User: `admin` / Pass: `admin`).
2.  **Khám phá dữ liệu (SQL Lab):**
    - Vào menu **SQL Lab** -> **SQL Editor**.
    - Chọn Database: `Olist Lakehouse (Spark)`.
    - Chọn Schema: `default`.
    - Chạy thử Query: `SELECT * FROM gold_rfm_segments LIMIT 10`.
3.  **Tạo Dataset:** 
    - Sau khi chạy query thành công, nhấn **Save** -> **Save Dataset**.
4.  **Tạo Chart:**
    - Vào menu **Datasets**, chọn dataset vừa tạo.
    - Chọn loại biểu đồ (Pie, Bar, Line, Map...).
    - Kéo thả các cột vào phần Metric/Group by và nhấn **Update Chart**.
5.  **Tạo Dashboard:**
    - Sau khi lưu Chart, chọn **Add to Dashboard** để tạo bảng điều khiển tổng hợp.

---

## 4. Thư viện Query SQL (Analytics Queries)

Dưới đây là các câu lệnh SQL tối ưu cho 4 biểu đồ mục tiêu:

### A. Tỉ lệ Phân khúc Khách hàng (RFM Segments)
*Dùng cho: Pie Chart*
```sql
SELECT 
    rfm_segment, 
    COUNT(customer_unique_id) as total_customers 
FROM default.gold_rfm_segments 
GROUP BY 1 
ORDER BY 2 DESC;
```

### B. Biến động Doanh thu Theo Tháng (Revenue Trend)
*Dùng cho: Line Chart / Area Chart*
```sql
SELECT 
    DATE_TRUNC('month', order_purchase_timestamp) as order_month, 
    SUM(price + freight_value) as total_revenue 
FROM default.silver_sales 
GROUP BY 1 
ORDER BY 1;
```

### C. Bản đồ Đơn hàng theo Bang (Geo Distribution)
*Dùng cho: Choropleth Map (Country: Brazil, ISO codes)*
```sql
SELECT 
    customer_state, 
    COUNT(DISTINCT order_id) as total_orders 
FROM default.silver_sales 
GROUP BY 1;
```

### D. Top 10 Danh mục Sản phẩm Doanh thu Cao nhất
*Dùng cho: Bar Chart*
```sql
SELECT 
    product_category_name as category, 
    SUM(price) as revenue 
FROM default.silver_sales 
WHERE product_category_name IS NOT NULL
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 10;
```

---
*Tài liệu này được tạo ra nhằm lưu trữ toàn bộ lịch sử xử lý kỹ thuật của task BDANGR20-27. Dự án Olist Lakehouse hiện đã hoàn thiện luồng dữ liệu E2E (End-to-End).*