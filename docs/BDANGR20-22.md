* **Mô tả:** Viết script ingest_[bronze.py](http://bronze.py) dùng Spark đọc dữ liệu CSV tải từ Kaggle và lưu vào bucket bronze trên MinIO dưới định dạng Delta.

* **Các bước triển khai (Step-by-step):**

  1. Download bộ dữ liệu Olist từ Kaggle (TOÀN BỘ DATASET 9 file: orders, order_items, products, customers, reviews, sellers, geolocation, order_payments, category_name_translation).

  * **Task Phụ:** Nạp toàn bộ 9 file dữ liệu Olist thay vì chỉ 5 file cốt lõi, giúp hệ thống hoàn thiện hơn ở các bước Silver/Gold sau này.

  2. Khởi tạo SparkSession với config kết nối S3/MinIO (spark.hadoop.fs.s3a.endpoint, v.v.) và enable Delta config (spark.sql.extensions=[io.delta](http://io.delta).sql.DeltaSparkSessionExtension).

  3. Dùng [spark.read](http://spark.read).csv(header=True, inferSchema=True) đọc từng file.

  4. Ghi xuống MinIO: df.write.format("delta").mode("overwrite").save("s3a://bronze/olist_orders/").

  5. Verify dữ liệu đã xuất hiện trong bucket bronze trên MinIO UI.

---

## BÁO CÁO THỰC HIỆN TASK & KẾ HOẠCH (TASK LOG)
*Trạng thái: Đã triển khai code, chờ bạn manual test và xác nhận kết quả.*

### 1. Đánh giá tính phù hợp và hướng triển khai
- Task hoàn toàn phù hợp với kiến trúc dự án (Medallion + Spark + MinIO + Delta).
- Quyết định triển khai theo hướng ingest **toàn bộ 9 file CSV** là tốt hơn cho các task Silver/Gold vì giữ đầy đủ dữ liệu nguồn ở tầng Bronze.
- Đã đồng bộ yêu cầu từ 5 file lên 9 file tại tài liệu quy trình để tránh lệch scope giữa docs và code.

### 2. Kế hoạch đã thực hiện
1. Đồng bộ yêu cầu tài liệu từ 5 file sang 9 file.
2. Tách cấu hình dùng chung vào `src/config.py`.
3. Tạo SparkSession builder dùng lại tại `src/spark_session.py`.
4. Viết job ingest Bronze tại `jobs/01_ingest_bronze.py` cho toàn bộ dataset.
5. Cập nhật README và task log với hướng dẫn manual test.

### 3. Quy trình thực hiện chi tiết (Step-by-step)
**Bước 1: Đồng bộ docs yêu cầu dữ liệu** (✅)
- Cập nhật `docs/overview-process.md` và nội dung task hiện tại để yêu cầu ingest full 9 file.

**Bước 2: Viết config dùng chung** (✅)
- Tạo các biến cấu hình MinIO/Spark/path dữ liệu tại `src/config.py`.
- Khai báo map 9 dataset CSV:
  - orders, order_items, products, customers, reviews, sellers, geolocation, order_payments, category_name_translation.

**Bước 3: Viết Spark session utility** (✅)
- Tạo hàm `get_spark_session()` tại `src/spark_session.py`.
- Bật đầy đủ Delta extension + Delta catalog.
- Set đầy đủ S3A config để Spark ghi MinIO qua `s3a://`.

**Bước 4: Viết job ingest Bronze** (✅)
- Viết `jobs/01_ingest_bronze.py` gồm:
  - Validate đủ 9 file nguồn trước khi chạy.
  - Đọc CSV bằng `header=true`, `inferSchema=true`.
  - Ghi Delta theo format `s3a://bronze/olist_<dataset_name>` với `mode=overwrite`.
  - Log tiến trình từng dataset và số lượng bản ghi.

**Bước 5: Đồng bộ README cho luồng full dataset** (✅)
- Cập nhật `README.md` để mô tả rõ 9 file bắt buộc và vị trí đặt file `data/raw/olist/`.
- Cập nhật cách chạy Bronze job đúng container hiện có.

### 4. Các file đã thay đổi
- `src/config.py`
- `src/spark_session.py`
- `jobs/01_ingest_bronze.py`
- `docs/overview-process.md`
- `README.md`
- `docs/BDANGR20-22.md`

### 5. Khó khăn và cách khắc phục
1. **Rủi ro import module khi chạy script bằng path file**
- Vấn đề: Chạy `python jobs/01_ingest_bronze.py` có thể không import được package `src` tùy context.
- Khắc phục: Thêm đoạn thêm `PROJECT_ROOT` vào `sys.path` trong job để đảm bảo import ổn định.

2. **Rủi ro sai endpoint MinIO giữa local và container**
- Vấn đề: Endpoint có thể truyền thiếu scheme hoặc khác môi trường.
- Khắc phục: Chuẩn hóa endpoint trong config (`http://...`) bằng hàm normalize.

3. **Hiệu năng do tạo SparkSession nhiều lần**
- Vấn đề: Tạo session mỗi file sẽ chậm và tốn tài nguyên.
- Khắc phục: Dùng 1 SparkSession duy nhất cho toàn bộ vòng lặp ingest.

### 6. Hướng dẫn manual test (bạn tự chạy)
1. Xác nhận thư mục `data/raw/olist/` có đủ 9 file CSV:
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_products_dataset.csv`
   - `olist_customers_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `olist_sellers_dataset.csv`
   - `olist_geolocation_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `product_category_name_translation.csv`
2. Chạy job ingest:
   - `python jobs/01_ingest_bronze.py`
   - Hoặc: `docker exec -it olist-pyspark-notebook python /home/jovyan/work/jobs/01_ingest_bronze.py`
3. Mở MinIO UI và kiểm tra bucket `bronze` có đủ 9 thư mục delta `olist_*`.
4. Kiểm tra trong mỗi thư mục có `_delta_log` và các file dữ liệu Delta.

### 7. Checklist định nghĩa hoàn thành (DoD)
- [ ] Yêu cầu task đã chuyển từ 5 file sang full 9 file và docs đã đồng bộ.
- [ ] Job `jobs/01_ingest_bronze.py` chạy thành công không lỗi.
- [ ] Bucket `bronze` có đủ 9 dataset dạng Delta.
- [ ] Mỗi dataset có `_delta_log` và file data được ghi mới.
- [ ] Log job hiển thị tiến trình ingest và số bản ghi từng dataset.

### 8. Trạng thái chờ
- Đang chờ bạn manual test theo checklist ở trên.
- Khi bạn gửi kết quả test, tôi sẽ cập nhật tiếp phần “lỗi thực tế và cách khắc phục thực tế” nếu có phát sinh.
