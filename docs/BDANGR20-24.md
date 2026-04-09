[Issue 4] Xây dựng Silver Layer (Data Cleansing & Denormalization)
* **Mô tả:** Viết script process_[silver.py](http://silver.py). Chuyển đổi dữ liệu thô thành dữ liệu có cấu trúc chuẩn, join các bảng lại với nhau để dễ dàng phân tích.

* **Các bước triển khai (Step-by-step):**

  1. Đọc dữ liệu từ Hive Catalog (spark.table("orders"), v.v.).

  2. **Làm sạch:** Xóa các đơn hàng có trạng thái canceled (bị hủy). Xử lý null ở cột order_delivered_customer_date.

  3. **Chuẩn hóa:** Ép kiểu các cột ngày tháng (order_purchase_timestamp) từ String sang kiểu Timestamp bằng hàm to_timestamp() của Spark.

  4. **Join bảng (Quan trọng):** Join orders + customers + order_items + products bằng các khóa ngoại (order_id, customer_id, product_id).

  5. Lưu Dataframe tổng hợp này vào S3: s3a://silver/denormalized_sales/ dưới dạng Delta.

  6. Nhờ Vân (Thành viên 4) register bảng này vào Hive Catalog tên là silver_sales.

---
---
## Kế hoạch triển khai (Implementation Plan)

### 1. Phân tích & Đề xuất chuẩn hóa
- **Mục tiêu:** Xây dựng bảng Silver denormalized (bảng phẳng) chứa đầy đủ thông tin về đơn hàng, khách hàng và sản phẩm phục vụ Analytics.
- **Xử lý Null ở `order_delivered_customer_date`:** Sử dụng hàm `coalesce` để điền ngày dự kiến giao hàng (`order_estimated_delivery_date`) cho các đơn hàng chưa có ngày giao thực tế. Điều này giúp giữ lại dữ liệu cho các đơn hàng đang vận chuyển.
- **Join Logic:** 
    - `orders` (Left Join) `customers` trên `customer_id`.
    - `orders` (Left Join) `order_items` trên `order_id`.
    - `order_items` (Left Join) `products` trên `product_id`.

### 2. Các bước triển khai chi tiết (Step-by-step)

#### Bước 1: Cấu hình hạ tầng
- Cập nhật file `src/config.py`:
    - Thêm biến `SILVER_BUCKET` lấy từ môi trường (mặc định: `silver`).
    - Thêm hàm `get_silver_table_path(dataset_name)` để trả về URI `s3a://silver/...`.

#### Bước 2: Khởi tạo Script xử lý (`jobs/02_process_silver.py`)
- Import các thư viện cần thiết: `pyspark.sql.functions` (col, coalesce, to_timestamp).
- Sử dụng function `get_spark_session()` đã có để kết nối Spark.

#### Bước 3: Đọc và Làm sạch dữ liệu
- Đọc các bảng từ Hive catalog: `olist_orders`, `olist_customers`, `olist_order_items`, `olist_products`.
- **Lọc:** Loại bỏ các đơn hàng có `order_status = 'canceled'`.
- **Xử lý Null:** Điền `order_delivered_customer_date` bằng `order_estimated_delivery_date`.

#### Bước 4: Chuẩn hóa kiểu dữ liệu
- Chuyển đổi các cột sau từ String sang Timestamp:
    - `order_purchase_timestamp`
    - `order_approved_at`
    - `order_delivered_carrier_date`
    - `order_delivered_customer_date`
    - `order_estimated_delivery_date`

#### Bước 5: Thực hiện Denormalization (Join)
- Thực hiện chuỗi Join để tạo ra DataFrame tổng hợp `silver_sales`.

#### Bước 6: Lưu trữ và Đăng ký Catalog
- Ghi DataFrame ra MinIO (S3) định dạng **Delta** tại đường dẫn `s3a://silver/denormalized_sales`.
- Sử dụng Spark SQL `CREATE TABLE IF NOT EXISTS default.silver_sales` để đăng ký bảng vào Hive Metastore.

### 3. Kế hoạch xác minh (Verification Plan)
- **Kiểm tra kỹ thuật:** Chạy script và kiểm tra logs xem có lỗi Join hoặc ghi dữ liệu không.
- **Kiểm tra dữ liệu:** 
    - Chạy lệnh SQL: `DESCRIBE TABLE default.silver_sales` để kiểm tra schema.
    - Truy vấn 10 dòng đầu: `SELECT * FROM default.silver_sales LIMIT 10`.
    - Kiểm tra xử lý null: Đảm bảo không còn dòng nào có `order_delivered_customer_date` bị null nếu đã có ngày dự kiến.

---
## Định nghĩa hoàn thành (Definition of Done)
Task được coi là hoàn tất khi:
- [x] Script `jobs/02_process_silver.py` thực hiện đúng logic: lọc canceled, xử lý null, cast type và join bảng.
- [x] Dữ liệu được lưu trữ tại `s3a://silver/denormalized_sales` dưới định dạng **Delta**.
- [x] Bảng `default.silver_sales` đã được đăng ký thành công trong Hive Metastore.
- [x] Có thể truy vấn dữ liệu từ bảng `silver_sales` với đầy đủ thông tin denormalized.
- [x] Không còn giá trị `null` ở cột `order_delivered_customer_date` (được thay bằng ngày dự kiến).

