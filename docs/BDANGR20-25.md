[Issue 5] Phân tích RFM (Recency, Frequency, Monetary) - Gold Layer
* **Mô tả:** Viết script analytics_[gold.py](http://gold.py). Áp dụng tư duy phân tích Big Data để tạo bảng phân khúc khách hàng bằng mô hình RFM.

* **Các bước triển khai (Step-by-step):**

  1. Đọc bảng silver_sales bằng Spark SQL.

  2. **Tính R (Recency):** Tìm ngày mua hàng gần nhất của từng KH. Lấy một ngày giả định (ví dụ: ngày max trong data + 1) trừ đi ngày mua gần nhất để ra số ngày (Dùng datediff).

  3. **Tính F (Frequency):** COUNT số lượng đơn hàng của từng KH.

  4. **Tính M (Monetary):** SUM tổng tiền (price + freight_value) của từng KH.

  5. Dùng hàm ntile(4) (Window Function) để chia R, F, M thành 4 quartile (từ 1 đến 4 điểm).

  6. Tổng hợp điểm RFM và phân loại (Ví dụ: Điểm 444 là Khách VIP).

  7. Ghi kết quả ra s3a://gold/rfm_segments/. Tối ưu hiệu năng: Thêm lệnh partitionBy("rfm_segment") khi ghi file.

---
### 📝 Kế hoạch thực hiện (Implementation Plan) - Chờ duyệt
**Người thực hiện:** Antigravity (AI Assistant)
**Ngày lập kế hoạch:** 2026-04-09

**1. Chuẩn bị & Cấu hình:**
- Cập nhật `src/config.py`: Thêm hằng số `GOLD_BUCKET = "gold"` và hàm `get_gold_table_path`.
- Đảm bảo bucket `gold` đã tồn tại trong MinIO (sẽ kiểm tra/tạo nếu cần).

**2. Phát triển Job `jobs/03_analytics_gold.py`:**
- **Bước 2.1:** Khởi tạo SparkSession với cấu hình Hive và S3A.
- **Bước 2.2:** Đọc bảng `default.silver_sales` từ Hive Metastore.
- **Bước 2.3:** Tổng hợp dữ liệu theo `customer_unique_id`:
    - `last_purchase_date = max(order_purchase_timestamp)`
    - `frequency = countDistinct(order_id)`
    - `monetary = sum(price + freight_value)`
- **Bước 2.4:** Tính toán RFM Metrics:
    - `reference_date = max(last_purchase_date) + 1 day` (Tính động từ data).
    - `recency = datediff(reference_date, last_purchase_date)`.
- **Bước 2.5:** Gán điểm RFM (ntile 4):
    - `r_score`: `ntile(4)` over `recency` DESC (4 là mới nhất).
    - `f_score`: `ntile(4)` over `frequency` ASC (4 là mua nhiều nhất).
    - `m_score`: `ntile(4)` over `monetary` ASC (4 là chi tiêu nhiều nhất).
    - `rfm_score = concat(r_score, f_score, m_score)`.
- **Bước 2.6:** Phân khúc khách hàng (`rfm_segment`):
    - 444: VIP/Champions
    - 4xx: New Customers/Recent
    - x4x: Loyal Customers
    - 1xx: Lost Customers
    - (Sẽ áp dụng bảng mapping chi tiết hơn).

**3. Lưu trữ & Đăng ký Metastore:**
- Ghi dữ liệu dạng Delta Lake vào đường dẫn tầng Gold.
- Sử dụng `partitionBy("rfm_segment")`.
- Câu lệnh SQL: `CREATE TABLE IF NOT EXISTS default.gold_rfm_segments ...`.

**4. Kiểm tra (Validation):**
- Đếm số lượng khách hàng theo từng segment.
- Kiểm tra tính logic: Khách hàng VIP phải có Monetary và Frequency thuộc nhóm cao nhất.

---
### ✅ Kết quả thực hiện (Results)
**Trạng thái:** Hoàn thành (2026-04-09)

**1. Các thay đổi chính:**
- Đã thêm `GOLD_BUCKET = "gold"` vào `src/config.py`.
- Đã triển khai `jobs/03_analytics_gold.py` với logic RFM chuẩn:
    - **Recency:** Tính từ ngày mua cuối cùng trong data + 1 ngày (2018-09-04).
    - **Scoring:** Sử dụng `ntile(4)` để gán điểm 1-4.
    - **Segmentation:** Phân loại khách hàng thành 7 nhóm (VIP, Loyal, Big Spender, Recent, At Risk, Lost, General).
- Đã đăng ký bảng `default.gold_rfm_segments` vào Hive Metastore.

**2. Thống kê phân khúc (Snapshot):**
| RFM Segment | Customer Count | Avg Monetary |
| :--- | :--- | :--- |
| **Champions/VIP** | 5,600 | 400.97 |
| **Loyal Customers** | 2,107 | 299.40 |
| **Big Spenders** | 16,465 | 388.10 |
| **Recent Customers** | 18,290 | 99.49 |
| **At Risk** | 17,713 | 89.16 |
| **Lost Customers** | 17,815 | 87.18 |
| **General Customers** | 17,570 | 89.42 |

**3. Đường dẫn lưu trữ:** `s3a://gold/rfm_segments/` (Định dạng Delta, Partition by `rfm_segment`).

---
### ✅ Định nghĩa hoàn thành (Definition of Done)
- [x] Script `jobs/03_analytics_gold.py` được triển khai đúng logic tính toán R, F, M.
- [x] Điểm RFM (r_score, f_score, m_score) được gán chính xác bằng `ntile(4)`.
- [x] Khách hàng được phân khúc vào các nhóm dựa trên điểm số (rfm_segment).
- [x] Dữ liệu được lưu trữ tại `s3a://gold/rfm_segments` dưới định dạng **Delta**.
- [x] Bảng `default.gold_rfm_segments` đã được đăng ký thành công trong Hive Metastore.
- [x] Có thể truy vấn và visualize kết quả trực tiếp từ Jupyter Notebook.
- [x] Phân phối dữ liệu hợp lý (Khách hàng VIP có Monetary và Frequency cao nhất).
