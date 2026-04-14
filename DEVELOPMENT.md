# Development Guide

## 1. Setup & Chạy dự án

1. Clone repository về máy:
   ```bash
   git clone https://github.com/darktheDE/Olist-E-Commerce-Lakehouse
   cd Olist-E-Commerce-Lakehouse
   ```
2. Cập nhật nhánh `main` mới nhất:
   ```bash
   git checkout main
   git pull origin main
   ```
3. **Tải Dataset:**
   - Tải bộ dữ liệu [Olist E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) từ Kaggle.
   - Giải nén và đặt tất cả các file CSV vào thư mục: `data/raw/olist/`
   - Đảm bảo thư mục có cấu trúc:
     ```text
     data/raw/olist/
     ├── olist_customers_dataset.csv
     ├── olist_geolocation_dataset.csv
     ├── ...
     ```
3. Khởi chạy các dịch vụ (Docker):
   ```bash
   docker compose up -d
   ```
4. Dừng các dịch vụ:
   ```bash
   docker compose down
   ```

## 2. Orchestration với Airflow

Dự án sử dụng Airflow để tự động hóa luồng dữ liệu (Bronze -> Silver -> Gold).

1. **Truy cập Airflow Web UI:**
   - URL: `http://localhost:8080`
   - Username: `admin`
   - Password: `admin`

2. **Kích hoạt Pipeline:**
   - Tìm DAG `olist_lakehouse_pipeline`.
   - Bật (unpause) DAG và nhấn nút "Trigger DAG" để chạy ngay lập tức.

3. **Giám sát:**
   - Sử dụng **Graph View** để xem luồng công việc.
   - Kiểm tra **Logs** của từng task (`ingest_bronze`, `process_silver`, `analytics_gold`) nếu gặp lỗi.


**Tiến hành Code:**
1. Đảm bảo bạn đang ở nhánh `main` và đã cập nhật mới nhất:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Thực hiện code và commit:
   ```bash
   git add .
   git commit -m "feat: mô tả ngắn gọn sửa đổi"
   git push origin main
   ```

## 3. Quy tắc đặt tên

### Nhánh (nếu sử dụng)
* `task/<mã-task>` - Công việc cụ thể
* `hotfix/...` - Sửa lỗi gấp trên main

### Commit
* `feat:` - Tính năng mới
* `fix:` - Sửa lỗi
* `docs:` - Tài liệu
* `refactor:` - Cải thiện / tối ưu code
* `chore:` - Tooling, setup no production code change
