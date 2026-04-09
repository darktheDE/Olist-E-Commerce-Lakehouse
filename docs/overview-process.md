# QUY TRÌNH PHÁT TRIỂN

## 1. MODULES (EPICS)

_Tạo các Module này trong Plane.so để phân nhóm công việc lớn._

### Module 1: Infrastructure & Data Ingestion (Bronze Layer)

* **Lead:** Đinh Trọng Đức Anh

* **Mục tiêu:** Xây dựng hạ tầng lưu trữ giả lập cloud (MinIO), cài đặt engine xử lý (Spark) và tự động hóa việc đẩy dữ liệu thô (Kaggle Olist) vào Data Lakehouse dưới định dạng chuẩn ACID.

* **Output mong muốn:** Hệ thống Docker Compose chạy ổn định các container. Dữ liệu CSV Olist được convert 100% sang định dạng Delta Lake nằm gọn trong bucket `bronze` của MinIO.

### Module 2: Data Processing & ETL (Silver Layer)

* **Lead:** Lê Văn Lộc

* **Mục tiêu:** Thực hiện quá trình chuyển đổi dữ liệu lõi. Làm sạch, loại bỏ nhiễu và kết hợp các bảng dữ liệu rời rạc thành các bảng phẳng (Denormalized) phục vụ phân tích.

* **Output mong muốn:** File script PySpark chạy thành công, sinh ra các bảng Delta ở bucket `silver`. Dữ liệu không còn giá trị Null sai lệch, định dạng thời gian được chuẩn hóa.

### Module 3: Advanced Business Analytics (Gold Layer)

* **Lead:** Nguyễn An Khang

* **Mục tiêu:** Áp dụng tư duy phân tích dữ liệu lớn để tính toán các chỉ số kinh doanh quan trọng (Đặc biệt là RFM và KPI vận chuyển) trên tập dữ liệu đã làm sạch.

* **Output mong muốn:** Các bảng tổng hợp (Aggregated Tables) cực kỳ tối ưu, sẵn sàng cho công cụ BI đọc trực tiếp nằm ở bucket `gold`.

### Module 4: Governance, Orchestration & BI (Consumption Layer)

* **Lead:** Vũ Kiều Thúy Vân

* **Mục tiêu:** Quản lý metadata, kết nối toàn bộ các đoạn script đơn lẻ thành một Data Pipeline chạy tự động, và trực quan hóa dữ liệu lên Dashboard.

* **Output mong muốn:** Hive Metastore hoạt động làm Catalog. 1 DAG Airflow chạy thông luồng từ Bronze -> Gold. Dashboard Superset với ít nhất 4 biểu đồ.

# 2. CYCLES (SPRINTS)

_Do dự án chỉ có 1 tuần (7 ngày), chia thành 2 Mini-Cycles để kiểm soát rủi ro._

### Cycle 1: Nền tảng & Tiền xử lý (Ngày 1 - Ngày 3)

* **Mục tiêu:** Dựng xong môi trường, dữ liệu phải chảy được từ Source (CSV) -> Bronze -> Silver. Cấu hình xong Metastore.

* **Target Date:** Hết ngày thứ 3.

* **Trạng thái:** Dữ liệu sẵn sàng để phân tích.

### Cycle 2: Phân tích, Tự động hóa & Báo cáo (Ngày 4 - Ngày 7)

* **Mục tiêu:** Hoàn thiện tính toán Gold Layer, ráp code vào Airflow, vẽ Dashboard và chốt file Báo cáo Word cuối kỳ.

* **Target Date:** Hết ngày thứ 7.

* **Trạng thái:** Đóng gói hoàn chỉnh dự án.

# 3. WORK ITEMS (ISSUES)

_Tạo các Issue này trong Plane.so, gán vào Module và Cycle tương ứng, tag tên người phụ trách._

## CYCLE 1 ISSUES (Ngày 1 - 3)

### [Issue 1] Thiết lập môi trường Local (Docker Compose)

* **Module:** Module 1

* **Assignee:** Đinh Trọng Đức Anh

* **Priority:** Urgent (Blocker)

* **Mô tả:** Xây dựng tệp `docker-compose.yml` để khởi chạy đồng thời các dịch vụ cần thiết cho Lakehouse, tránh việc phải cài đặt tay trên từng máy thành viên.

* **Các bước triển khai (Step-by-step):**

  1. Tạo project folder. Viết file `docker-compose.yml`.

  2. Định nghĩa service **MinIO** (port 9000:9000 và 9001:9001). Cấu hình Access Key, Secret Key mặc định (`minioadmin`).

  3. Định nghĩa service **Jupyter/Pyspark-notebook** (để các thành viên viết code nháp). Map volume thư mục code vào container.

  4. Định nghĩa service **PostgreSQL** (để làm backend lưu metadata cho Hive).

  5. Khởi chạy `docker-compose up -d`. Truy cập MinIO UI, tạo thủ công 3 buckets: `bronze`, `silver`, `gold`.

* **Tài liệu tham khảo:** Search Google: _"docker compose minio spark hive"_.

### [Issue 2] Ingest Olist Dataset (CSV -> Bronze Layer)

* **Module:** Module 1

* **Assignee:** Đinh Trọng Đức Anh

* **Priority:** High

* **Mô tả:** Viết script `ingest_bronze.py` dùng Spark đọc dữ liệu CSV tải từ Kaggle và lưu vào bucket `bronze` trên MinIO dưới định dạng Delta.

* **Các bước triển khai (Step-by-step):**

  1. Download bộ dữ liệu Olist từ Kaggle (chọn khoảng 5 file cốt lõi: `orders`, `order_items`, `products`, `customers`, `reviews`).

  2. Khởi tạo `SparkSession` với config kết nối S3/MinIO (`spark.hadoop.fs.s3a.endpoint`, v.v.) và enable Delta config (`spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension`).

  3. Dùng `spark.read.csv(header=True, inferSchema=True)` đọc từng file.

  4. Ghi xuống MinIO: `df.write.format("delta").mode("overwrite").save("s3a://bronze/olist_orders/")`.

  5. Verify dữ liệu đã xuất hiện trong bucket `bronze` trên MinIO UI.

### [Issue 3] Cấu hình Hive Metastore (Data Catalog)

* **Module:** Module 4

* **Assignee:** Vũ Kiều Thúy Vân

* **Priority:** High (Cần làm song song để người 2 & 3 có thể query SQL)

* **Mô tả:** Thiết lập Hive Metastore để quản lý metadata (bảng, schema) của các Delta Tables, giúp các thành viên có thể dùng `spark.sql("SELECT * FROM ...")` thay vì đọc đường dẫn vật lý.

* **Các bước triển khai (Step-by-step):**

  1. Bổ sung cấu hình Hive vào file `spark-defaults.conf` (hoặc ngay trong lúc tạo SparkSession). Bật cờ `spark.sql.catalogImplementation=hive`.

  2. Viết 1 script nhỏ `register_tables.py` để khai báo các bảng ở bucket Bronze vào Catalog.

  3. _Ví dụ code:_ `spark.sql("CREATE TABLE IF NOT EXISTS default.orders USING DELTA LOCATION 's3a://bronze/olist_orders'")`.

  4. Test thử bằng cách chạy lệnh SQL `SHOW TABLES;`.

### [Issue 4] Xây dựng Silver Layer (Data Cleansing & Denormalization)

* **Module:** Module 2

* **Assignee:** Lê Văn Lộc

* **Priority:** High

* **Mô tả:** Viết script `process_silver.py`. Chuyển đổi dữ liệu thô thành dữ liệu có cấu trúc chuẩn, join các bảng lại với nhau để dễ dàng phân tích.

* **Các bước triển khai (Step-by-step):**

  1. Đọc dữ liệu từ Hive Catalog (`spark.table("orders")`, v.v.).

  2. **Làm sạch:** Xóa các đơn hàng có trạng thái `canceled` (bị hủy). Xử lý null ở cột `order_delivered_customer_date`.

  3. **Chuẩn hóa:** Ép kiểu các cột ngày tháng (`order_purchase_timestamp`) từ String sang kiểu `Timestamp` bằng hàm `to_timestamp()` của Spark.

  4. **Join bảng (Quan trọng):** Join `orders` + `customers` + `order_items` + `products` bằng các khóa ngoại (`order_id`, `customer_id`, `product_id`).

  5. Lưu Dataframe tổng hợp này vào S3: `s3a://silver/denormalized_sales/` dưới dạng Delta.

  6. Nhờ Vân (Thành viên 4) register bảng này vào Hive Catalog tên là `silver_sales`.

## CYCLE 2 ISSUES (Ngày 4 - 7)

### [Issue 5] Phân tích RFM (Recency, Frequency, Monetary) - Gold Layer

* **Module:** Module 3

* **Assignee:** Nguyễn An Khang

* **Priority:** High

* **Mô tả:** Viết script `analytics_gold.py`. Áp dụng tư duy phân tích Big Data để tạo bảng phân khúc khách hàng bằng mô hình RFM.

* **Các bước triển khai (Step-by-step):**

  1. Đọc bảng `silver_sales` bằng Spark SQL.

  2. **Tính R (Recency):** Tìm ngày mua hàng gần nhất của từng KH. Lấy một ngày giả định (ví dụ: ngày max trong data + 1) trừ đi ngày mua gần nhất để ra số ngày (Dùng `datediff`).

  3. **Tính F (Frequency):** `COUNT` số lượng đơn hàng của từng KH.

  4. **Tính M (Monetary):** `SUM` tổng tiền (price + freight_value) của từng KH.

  5. Dùng hàm `ntile(4)` (Window Function) để chia R, F, M thành 4 quartile (từ 1 đến 4 điểm).

  6. Tổng hợp điểm RFM và phân loại (Ví dụ: Điểm 444 là Khách VIP).

  7. Ghi kết quả ra `s3a://gold/rfm_segments/`. Tối ưu hiệu năng: Thêm lệnh `partitionBy("rfm_segment")` khi ghi file.

### [Issue 6] Thiết kế Airflow DAG (Orchestration)

* **Module:** Module 4

* **Assignee:** Vũ Kiều Thúy Vân

* **Priority:** Medium

* **Mô tả:** Thay vì chạy script bằng tay, cấu hình Airflow để chạy tự động theo luồng Bronze -> Silver -> Gold.

* **Các bước triển khai (Step-by-step):**

  1. Cài đặt Airflow (local hoặc thêm vào file docker-compose).

  2. Tạo file `olist_lakehouse_dag.py` trong thư mục dags.

  3. Sử dụng `BashOperator` hoặc `SparkSubmitOperator` để gọi tuần tự 3 file script: `ingest_bronze.py` >> `process_silver.py` >> `analytics_gold.py`.

  4. Bật Airflow Web UI, kích hoạt DAG và chụp lại biểu đồ Gantt/Graph để đưa vào báo cáo.

### [Issue 7] Trực quan hóa dữ liệu (Superset/PowerBI)

* **Module:** Module 4

* **Assignee:** Vũ Kiều Thúy Vân (có thể Khang hỗ trợ)

* **Priority:** High

* **Mô tả:** Kết nối công cụ BI vào lớp Gold để tạo Dashboard.

* **Các bước triển khai (Step-by-step):**

  1. Khởi chạy Apache Superset (hoặc dùng PowerBI desktop nếu Superset quá nặng).

  2. Kết nối với Spark SQL qua Thrift Server (nếu dùng Superset) hoặc dùng ODBC (nếu dùng PowerBI).

  3. Vẽ 4 biểu đồ:

     * Biểu đồ tròn (Pie chart): Tỉ lệ các nhóm khách hàng (VIP vs Churn) từ bảng RFM.

     * Biểu đồ đường (Line chart): Xu hướng doanh thu theo tháng.

     * Bản đồ (Map): Mật độ đơn hàng theo các bang (State) của Brazil.

     * Bảng (Table): Top 10 sản phẩm mang lại doanh thu cao nhất.

  4. Sắp xếp thành 1 Dashboard hoàn chỉnh, chụp ảnh màn hình đẹp.

### [Issue 8] Đóng gói Báo Cáo Cuối Kỳ (Word .docx)

* **Module:** All Modules

* **Assignee:** Cả nhóm

* **Priority:** Critical

* **Mô tả:** Tổng hợp toàn bộ công việc vào file Word theo đúng form của giảng viên. Cần thể hiện rõ vai trò từng người.

* **Các bước triển khai (Step-by-step):**

  1. **Vân:** Viết phần mở đầu, kiến trúc Lakehouse 5 lớp, vẽ diagram, giới thiệu Airflow & Superset. (Cấu trúc tài liệu).

  2. **Đức Anh:** Viết Chương Ingestion & Storage. Chụp ảnh config MinIO, giải thích định dạng Delta và lợi ích của Storage Layer.

  3. **Lộc:** Viết Chương Processing Layer. Chụp code Spark DataFrame, giải thích tại sao dùng Spark thay vì MapReduce để join dữ liệu lớn.

  4. **Khang:** Viết Chương Analytics (Gold). Cắt nghĩa logic tính RFM, giải thích Window Functions trong Spark SQL. Đánh giá tính ứng dụng kinh doanh.

  5. **Review chéo:** Cả 4 người đọc lại file, kiểm tra lỗi chính tả, format lại bảng phân công công việc và danh sách tài liệu tham khảo theo đúng chuẩn của trường.

# 4. QUẢN TRỊ RỦI RO & PHƯƠNG ÁN DỰ PHÒNG (FALLBACKS)

Do kiến trúc Big Data Lakehouse bao gồm nhiều thành phần đồ sộ và đòi hỏi tài nguyên máy tính lớn, dưới đây là các kịch bản sự cố có thể xảy ra và phương án giải quyết:

### 4.1 Rủi ro: Quá tải RAM / CPU (Out of Memory)
- **Vấn đề:** Khởi chạy toàn bộ file `docker-compose.yml` (MinIO, Spark, Postgres, Hive, Airflow, Superset) trên máy cá nhân có dung lượng RAM dưới 16GB sẽ gây hiện tượng lag, crash hoặc container bị `OOMKilled`.
- **Phương án (Fallback):** 
  - Khởi tạo từng phần theo lịch trình task (Cycle). Trong Cycle 1, chỉ bật MinIO, Postgres và Jupyter/Spark.
  - Tắt hẳn Airflow và Superset khi đang trong quá trình viết code Spark ETL.
  - Tại bước báo cáo cuối cùng, ưu tiên build dữ liệu ra thành bảng cuối ở dạng `.csv` hoặc Parquet để báo cáo thay vì duy trì dashboard thời gian thực nếu máy không đủ tải.

### 4.2 Rủi ro: Cấu hình Airflow phức tạp, không liên kết được với Spark
- **Vấn đề:** Airflow chạy trong Docker không thể connect và submit job lên Spark cluster hoặc gây ra các lỗi đường dẫn thư mục phức tạp trong vài ngày cuối.
- **Phương án (Fallback):** 
  - Không bắt buộc dùng Airflow Orchestration trong báo cáo nếu mất quá nhiều thời gian sửa lỗi cấu hình.
  - Tạo một Bash script đơn giản (`run_pipeline.sh`) để chạy nối tiếp các file python:
    ```bash
    #!/bin/bash
    python ingest_bronze.py && python process_silver.py && python analytics_gold.py
    ```
  - Chụp ảnh log console báo thành công và giải trình (trong báo cáo) đây là giải pháp manual thay thế cho orchestration tự động.

### 4.3 Rủi ro: Lỗi kết nối Spark - MinIO / Hive Metastore
- **Vấn đề:** Không lưu được file hoặc không đọc được schema từ Hive بسبب lỗi xung đột thư viện `hadoop-aws` hoặc Thrift server timeout.
- **Phương án (Fallback):**
  - Bỏ qua Hive Metastore (Data Catalog). Thay vì dùng `spark.sql("SELECT * FROM silver_sales")`, hãy dùng đường dẫn vật lý: `spark.read.format("delta").load("s3a://silver/denormalized_sales/")`.
  - Nếu kết nối `s3a://` (MinIO) liên tục lỗi, tạm thời map một thư mục local làm object storage giả lập `file:///tmp/datalake/` để giữ tiến độ dự án.

### 4.4 Rủi ro: Apache Superset nặng hoặc cấu hình ODBC lỗi
- **Vấn đề:** Superset không connect được với Spark SQL bằng Thrift Server.
- **Phương án (Fallback):**
  - Đổi công cụ BI. Connect trực tiếp các bảng kết quả ở lớp Gold (sau khi tải xuống thành file CSV hoặc Parquet) bằng **Microsoft Power BI** hoặc Tableau Desktop để vẽ Dashboard. Vì output đã được tổng hợp ở quy mô kinh doanh nên kích thước file khá nhỏ, hoàn toàn tương thích với các công cụ này.

# 5. TECHNICAL SOLUTIONS & BEST IMPLEMENTATIONS (Tối ưu hóa Kỹ thuật)

Dưới đây là các giải pháp kỹ thuật "chuẩn thực tế" (Best Practices/Implementations) nhằm đảm bảo dự án chạy trơn tru, không lãng phí thời gian cấu hình và tránh các điểm nghẽn hệ thống:

### 5.1 Kiến trúc Triển khai (Docker Compose Phasing)
**Vấn đề:** Chạy đồng thời toàn bộ Stack cài đặt (MinIO, Spark, Postgres, Airflow, Superset) trên máy cá nhân sẽ dẫn đến việc tiêu tốn RAM, CPU cực lớn và rủi ro OOM (Out Of Memory).
**Solution:** Phân chia Docker Compose thành các profiles hoặc file riêng biệt tương ứng với từng giai đoạn (Cycle):
- **Giai đoạn Code (Data Engineering - Cycle 1):** Chỉ khởi chạy **MinIO** và **Jupyter/PySpark**. Không đụng đến Airflow hay Superset vào thời điểm này.
- **Giai đoạn BI (Analytics - Cycle 2):** Khởi chạy **Superset** để connect.
Tạm thời Comment-out (hoặc dùng docker profile) với Airflow nếu cảm thấy quá nặng.

### 5.2 Xử lý Kết nối Spark - MinIO (Spike Task)
**Vấn đề:** Lỗi "Class Not Found" hoặc "S3 endpoint unresolvable" là lỗi rất phổ biến khi setup Spark kết nối với S3/MinIO nếu các thư viện JAR (`hadoop-aws`, `aws-java-sdk`, `delta-spark`) không tương thích version.
**Solution:** Trước khi đi vào viết Logic Ingest (Issue 2), Team Lead cần phải thực hiện một **Spike Task (PoC)**: 
- Viết 1 file script siêu nhỏ để test Ping từ Spark qua MinIO (ví dụ: tạo 1 biến list chứa chuỗi `"Hello World"`, viết thành định dạng txt/csv lưu thẳng lên MinIO bucket). 
- Chỉ khi nào script này ghi và đọc lại thành công thì nhóm mới bắt tay vào code các file `ingest_bronze.py` hay `process_silver.py`.

### 5.3 Lắp đặt Data Catalog - Dùng Local Derby thay phiên bản Postgres
**Vấn đề:** Cấu hình Postgres làm Database Backend cho Hive Metastore là overkill (vượt quá mức cần thiết) cho dự án vỏn vẹn 7 ngày, dễ phát sinh lỗi authentication và JDBC connection.
**Solution:** Tận dụng **Local Derby Database** (mặc định của Apache Spark).
- Bỏ service PostgreSQL trong cấu trúc Docker.
- Chỉ cần ánh xạ (Map Volume) thư mục `metastore_db` từ trong container Spark ra ngoài thư mục máy thật để sau khi restart Docker, metadata của bạn (như Hive tables) không bị thổi bay. 
- Vừa nhẹ tài nguyên máy, vừa tiết kiệm thời gian cấu hình mà vẫn đạt 100% mục tiêu của lớp Data Catalog (Metadata Management).
