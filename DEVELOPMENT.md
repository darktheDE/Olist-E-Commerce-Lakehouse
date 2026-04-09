# Development Guide

## 1. Setup & Chạy dự án

1. Clone repository về máy:
   ```bash
   git clone https://github.com/darktheDE/Olist-E-Commerce-Lakehouse
   cd Olist-E-Commerce-Lakehouse
   ```
2. Chuyển sang nhánh `develop` và cập nhật:
   ```bash
   git checkout develop
   git pull origin develop
   ```
3. Khởi chạy các dịch vụ (Docker):
   ```bash
   docker-compose up -d
   ```
4. Dừng các dịch vụ:
   ```bash
   docker-compose down
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

## 2. Quy trình phát triển (Agile/Scrum với Plane.so)

**Chuẩn bị Task:**
1. Lên Plane.so chọn task cần làm.
2. Đọc tài liệu lệnh quan (`DEVELOPMENT.md`, yêu cầu của task).
3. Assign task cho chính mình (Assignee).
4. Assign người Reviewer.
5. Đặt Deadline hoàn thành code cho người làm (đến khi có PR).
6. Chuyển trạng thái task từ `Todo` sang `In Progress`.

**Tiến hành Code:**
1. Cập nhật nhánh `develop` mới nhất:
   ```bash
   git checkout develop
   git pull origin develop
   ```
2. Tạo nhánh từ `develop` theo format `feature/<module>/<mã-task-trên-plane>`:
   ```bash
   git checkout -b feature/<module>/<mã-task>
   ```
3. Tạo file `<mã-task>.md` để lưu lại quá trình phát triển (cách đã làm, lỗi gặp phải, cách fix) làm tài liệu lưu trữ sau này.
4. Thực hiện code và commit:
   ```bash
   git add .
   git commit -m "feat: mô tả ngắn gọn sửa đổi"
   ```
5. Đẩy code lên repository:
   ```bash
   git push origin feature/<module>/<mã-task>
   ```

**Pull Request (PR) & Code Review:**
1. Tạo PR từ nhánh `feature/...` vào nhánh `develop`.
2. Đặt Deadline cho Reviewer (thời gian tối đa để kiểm tra và Accept PR).
3. Reviewer kiểm tra code và duyệt qua.
4. Quản lý repo tiến hành Merge PR khi hoàn tất review 3 bên.

**Lịch Họp:**
* Họp nhóm 2 ngày/buổi, vào **22h30 mỗi tối**.

## 3. Quy tắc đặt tên

### Nhánh (Branch)
* `feature/<module>/<task>` - Tính năng / công việc mới
* `bugfix/...` - Sửa lỗi
* `chore/...` - Cập nhật thư viện, cấu hình

### Commit
* `feat:` - Tính năng mới
* `fix:` - Sửa lỗi
* `docs:` - Tài liệu
* `refactor:` - Cải thiện / tối ưu code
* `chore:` - Tooling, setup no production code change
