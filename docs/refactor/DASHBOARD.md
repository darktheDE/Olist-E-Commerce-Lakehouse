# Hướng dẫn vẽ Dashboard trên Superset & Các Query Insight Cốt Lõi

Dựa trên kết quả xây dựng Gold layer và tài liệu Task 27, dưới đây là danh sách các Query Insight cốt lõi để xây dựng báo cáo E-Commerce, kèm theo hướng dẫn cấu hình từng loại biểu đồ (chart) trên Superset.

---

## 1. Danh sách các Query Insight Cốt Lõi

### 1.1. Tỉ lệ Phân khúc Khách hàng (RFM Segments)
**Mục đích:** Hiểu rõ cơ cấu khách hàng (khách hàng trung thành, khách hàng có nguy cơ rời bỏ, v.v.)
```sql
SELECT 
    rfm_segment, 
    COUNT(customer_unique_id) as total_customers 
FROM default.gold_rfm_segments 
GROUP BY 1 
ORDER BY 2 DESC;
```

### 1.2. Biến động Doanh thu Theo Tháng (Revenue Trend)
**Mục đích:** Theo dõi sự tăng trưởng doanh thu theo thời gian để phát hiện tính thời vụ.
```sql
SELECT 
    DATE_TRUNC('month', order_purchase_timestamp) as order_month, 
    SUM(price + freight_value) as total_revenue 
FROM default.silver_sales 
GROUP BY 1 
ORDER BY 1;
```

### 1.3. Tổng quan Chỉ số Chính (Key Metrics)
**Mục đích:** Hiển thị các chỉ số quan trọng (Big Numbers) như Tổng doanh thu, Tổng số đơn hàng.
```sql
-- Tổng Doanh Thu
SELECT SUM(price + freight_value) as total_revenue FROM default.silver_sales;

-- Tổng Số Đơn Hàng
SELECT COUNT(DISTINCT order_id) as total_orders FROM default.silver_sales;
```

### 1.4. Top 10 Danh mục Sản phẩm Doanh thu Cao nhất
**Mục đích:** Xác định các sản phẩm mang lại giá trị cao nhất.
```sql
SELECT 
    product_category_name as category, 
    SUM(price + freight_value) as revenue 
FROM default.silver_sales 
WHERE product_category_name IS NOT NULL
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 10;
```

### 1.5. Phân bổ Đơn hàng theo Bang (Geo/State Distribution)
**Mục đích:** Xem xét khu vực nào mang lại nhiều đơn hàng nhất.
```sql
SELECT 
    customer_state, 
    COUNT(DISTINCT order_id) as total_orders 
FROM default.silver_sales 
GROUP BY 1
ORDER BY 2 DESC;
```

---

## 2. Hướng dẫn Step-by-Step vẽ Biểu đồ bằng Superset

Lưu ý chung: Đối với mỗi biểu đồ, bạn cần chạy Query tương ứng trong **SQL Lab**, sau đó chọn **Save > Save Dataset**, và cuối cùng chọn **Create Chart** trên dataset đó để tiến hành các bước kéo thả Field.

### 2.1. PIE CHART - Tỉ lệ Phân khúc Khách hàng (RFM)
**Sử dụng Query:** 1.1

*   **Chart Type:** Pie Chart
*   **Dimensions:** Kéo cột `rfm_segment` vào mục Dimensions.
*   **Metric:** Kéo cột `total_customers` vào mục Metric (Tùy chọn tính toán là `SUM`).
*   **Filters:** (Bỏ trống)
*   **Row limit:** (Để trống hoặc giới hạn hiển thị nếu có quá nhiều segments).
*   **Sort by metric:** Tích chọn (Sắp xếp các biểu đồ rẻ quạt theo kích cỡ từ lớn đến bé).

### 2.2. LINE CHART / AREA CHART - Biến động Doanh thu Theo Tháng
**Sử dụng Query:** 1.2

*   **Chart Type:** Line Chart hoặc Area Chart
*   **X-axis:** Kéo cột `order_month` vào mục X-axis.
*   **X-Axis Sort By:** Chọn `order_month` hoặc để trống (để Superset giữ nguyên chuỗi thời gian tăng dần).
*   **Metrics:** Kéo cột `total_revenue` vào mục Metrics (Chọn aggregate là `SUM`).
*   **Dimensions:** (Bỏ trống - trừ khi bạn muốn phân tách chuỗi doanh thu theo từng bang/danh mục).
*   **Contribution Mode:** None.
*   **Filters:** (Bỏ trống)
*   **Series limit:** None.
*   **Sort query by:** (Bỏ trống).
*   **Row limit:** (Mặc định).

### 2.3. BIG NUMBER - Tổng Doanh Thu / Tổng Số Đơn Hàng
**Sử dụng Query:** 1.3

*   **Chart Type:** Big Number
*   **Metric:** Kéo cột `total_revenue` (hoặc `total_orders`) vào mục Metric, aggregate là `SUM`.
*   **Filters:** (Bỏ trống).
*   *Lưu ý: Thường chỉ hiển thị một con số tổng kết, có thể kết hợp Big Number with Trendline nếu có cột thời gian.*

### 2.4. BAR CHART - Top 10 Danh mục Sản phẩm Doanh thu Cao nhất
**Sử dụng Query:** 1.4

*   **Chart Type:** Bar Chart
*   **X-axis:** Kéo cột `category` vào mục X-axis.
*   **X-Axis Sort By:** Tùy chọn `revenue` để cột cao nất đứng lên đầu.
*   **Metrics:** Kéo cột `revenue` vào mục Metrics, aggregate `SUM`.
*   **Dimensions:** (Bỏ trống).
*   **Filters:** (Bỏ trống)
*   **Series limit:** None (do ta đã LIMIT 10 ở trong query SQL rồi).
*   **Sort query by:** (Bỏ trống).

### 2.5. TABLE - Phân bổ Đơn hàng theo Bang
**Sử dụng Query:** 1.5

*   **Chart Type:** Table
*   **Query mode:** Chọn `Raw records` (Dữ liệu đã được group by từ query nên chỉ cần hiển thị thô).
*   **Columns:** Kéo 2 cột `customer_state` và `total_orders` vào phần Columns.
*   **Filters:** (Bỏ trống).
*   **Ordering:** Nhấp vào tên cột để tùy chọn sắp xếp (Descending / Ascending) theo `total_orders`.
*   **Server pagination:** (Tùy chọn).
*   **Row limit:** 1000 (Hiển thị hết số bang của Brazil).