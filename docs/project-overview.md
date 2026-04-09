# TÀI LIỆU TỔNG QUAN DỰ ÁN CUỐI KỲ

**Môn học:** Phân tích dữ liệu lớn (Big Data Analysis)\
**Nhóm thực hiện:** Nhóm 22\
**Giảng viên phụ trách:** ThS. Lê Thị Minh Châu

## 1. TÊN ĐỀ TÀI

**Xây dựng hệ thống Data Lakehouse phân tích hành vi khách hàng và hiệu suất kinh doanh thương mại điện tử (Dựa trên tập dữ liệu Olist)**

## 2. MỤC TIÊU DỰ ÁN

Dự án nhằm mục đích thiết kế và hiện thực hóa một đường ống dữ liệu lớn (Big Data Pipeline) hoàn chỉnh dựa trên **Kiến trúc Data Lakehouse**. Hệ thống sẽ giải quyết bài toán tích hợp, xử lý và phân tích khối lượng lớn dữ liệu rời rạc từ hệ thống thương mại điện tử, từ đó trích xuất các thông tin có giá trị phục vụ cho việc ra quyết định kinh doanh.

**Các mục tiêu cụ thể:**

* Áp dụng chuẩn kiến trúc **Medallion (Bronze - Silver - Gold)** để quản lý vòng đời dữ liệu.

* Sử dụng **Apache Spark** làm engine xử lý lõi thay thế cho các công nghệ cũ (MapReduce/Pig), đảm bảo hiệu năng xử lý phân tán tốc độ cao.

* Khai thác tính năng ACID của định dạng **Delta Lake** kết hợp lưu trữ object **MinIO**.

* Thực hiện phân tích kinh doanh chuyên sâu: **Mô hình RFM (Phân khúc khách hàng)** và **Phân tích hiệu suất giao hàng**.

## 3. DỮ LIỆU ĐẦU VÀO

* **Nguồn dữ liệu:** Bộ dữ liệu _Brazilian E-Commerce Public Dataset by Olist_ (Kaggle).

* **Đặc điểm:** Bao gồm hơn 100.000 đơn hàng với dữ liệu được phân tán trong nhiều bảng (CSV) khác nhau như: Thông tin khách hàng (`customers`), Đơn hàng (`orders`), Sản phẩm (`products`), Đánh giá (`reviews`), và Tọa độ địa lý (`geolocation`). Đây là bộ dữ liệu có tính quan hệ phức tạp, rất lý tưởng để thử nghiệm hiệu năng Join và Aggregation của Apache Spark.

## 4. KIẾN TRÚC HỆ THỐNG (ÁP DỤNG 05 LỚP LAKEHOUSE)

Hệ thống được thiết kế bám sát 5 lớp chức năng của kiến trúc Lakehouse hiện đại:

1. **Lớp Ingestion (Thu thập):** Apache Spark đóng vai trò đọc dữ liệu thô (Batch processing) từ các tệp CSV.

2. **Lớp Storage (Lưu trữ):** **MinIO** (tương thích S3) là nơi lưu trữ trung tâm. Dữ liệu được lưu dưới định dạng **Delta Lake** để đảm bảo tính toàn vẹn và hỗ trợ cập nhật linh hoạt.

3. **Lớp Metadata (Siêu dữ liệu):** Sử dụng **Hive Metastore** làm Data Catalog trung tâm, giúp chuẩn hóa schema và cho phép các công cụ khác truy vấn dữ liệu như những bảng SQL thực thụ.

4. **Lớp API / Processing Engine:** **Apache Spark (Spark SQL, DataFrame API)** chịu trách nhiệm thực hiện các tác vụ ETL phức tạp, biến đổi dữ liệu qua các tầng.

5. **Lớp Consumption (Tiêu thụ):** **Apache Superset** kết nối qua Hive/Spark Thrift Server để tạo các Dashboard trực quan hóa tương tác.

## 5. LUỒNG XỬ LÝ DỮ LIỆU (DATA PIPELINE)

Luồng xử lý được điều phối tự động (Orchestration) thông qua **Apache Airflow**, đi qua 3 tầng dữ liệu cốt lõi:

* **Tầng Bronze (Raw Data):** Ingest toàn bộ file CSV gốc, ép kiểu dữ liệu cơ bản và lưu trữ dưới dạng Delta Table.

* **Tầng Silver (Cleaned & Joined Data):** Làm sạch dữ liệu (xử lý Null, Duplicate), chuẩn hóa định dạng thời gian (Timestamp), và thực hiện Join các bảng rời rạc (Orders, Products, Customers) thành bảng phẳng (Denormalized Table) để tối ưu cho phân tích.

* **Tầng Gold (Business-level Data):** Chứa các bảng đã được tổng hợp, phục vụ trực tiếp cho báo cáo:

  * Bảng `gold_rfm_segments`: Tính toán điểm Recency, Frequency, Monetary để phân khúc khách hàng (VIP, Tiềm năng, Sắp rời bỏ).

  *
