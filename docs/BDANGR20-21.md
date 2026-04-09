# BDANGR20-21 - Issue 1: Thiết lập môi trường Local (Docker Compose)

## 1. Mục tiêu

Thiết lập môi trường local để cả nhóm chạy nhanh stack nền tảng Lakehouse, không cần cài tay từng thành phần.

## 2. Phạm vi

Trong phạm vi Issue 1:
- MinIO
- PostgreSQL
- Jupyter/PySpark Notebook
- Tự động tạo 3 bucket: bronze, silver, gold

Ngoài phạm vi Issue 1:
- Airflow
- Superset
- Hive Metastore service đầy đủ

## 3. Kết quả triển khai

Đã cập nhật các file:
- docker-compose.yml
- .env
- .env.example
- conf/spark-defaults.conf
- .gitignore
- docs/BDANGR20-21.md

Thiết kế chính:
- 4 service: minio, init-minio, postgres, pyspark-notebook
- Dùng volume để giữ dữ liệu sau restart
- Dùng .env để tách cấu hình local
- init-minio tự động tạo bucket khi MinIO sẵn sàng

## 4. Lưu ý quan trọng về credentials

- Không cần AWS account.
- Không cần lấy key từ AWS.
- Spark dùng giao thức S3A để kết nối MinIO local.
- MINIO_ROOT_USER và MINIO_ROOT_PASSWORD trong .env là thông tin local.
- JUPYTER_TOKEN là token local do team tự đặt, không phải token từ dịch vụ bên ngoài.

## 5. Lỗi đã gặp và cách xử lý (tóm tắt)

1. YAML parse error
- Nguyên nhân: thụt dòng YAML không chuẩn.
- Xử lý: chuẩn hóa indentation bằng spaces, chỉnh lại command block cho init-minio.

2. Nhầm lẫn AWS key
- Nguyên nhân: tên biến kiểu AWS gây hiểu nhầm.
- Xử lý: dùng trực tiếp MINIO_ROOT_USER/MINIO_ROOT_PASSWORD cho S3A config.

## 6. Hướng dẫn manual test

Tiền điều kiện:
1. Có file .env ở root project.
2. Port 9000, 9001, 5432, 8888 chưa bị chiếm.

Lệnh bạn tự chạy:
1. docker compose config
2. docker compose up -d
3. docker compose ps
4. docker compose logs init-minio
5. docker compose logs pyspark-notebook

Nếu không thấy bucket sau khi `up -d`, chạy thêm:
1. docker compose rm -f init-minio
2. docker compose up -d init-minio
3. docker compose logs init-minio

Kỳ vọng log có các dòng:
- `[init-minio] Creating buckets...`
- `[init-minio] Bucket list:`
- `bronze/`
- `silver/`
- `gold/`

Kiểm tra UI:
1. MinIO: http://localhost:9001
2. Jupyter: http://localhost:8888

Smoke test trong notebook:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("smoke-minio").getOrCreate()
df = spark.createDataFrame([(1, "ok")], ["id", "status"])
df.write.mode("overwrite").parquet("s3a://bronze/smoke-test/")
print("write_ok")
```

## 7. Checklist nghiệm thu (Done)

- [ ] `docker compose config` không báo lỗi parse/substitution.
- [ ] `docker compose up -d` chạy đủ 4 container.
- [ ] `docker compose ps` hiển thị:
  - minio: Up
  - postgres: Up (healthy)
  - pyspark-notebook: Up
  - init-minio: Exited (0)
- [ ] `docker compose logs init-minio` có thông báo tạo/đã tồn tại 3 bucket.
- [ ] MinIO UI đăng nhập được và thấy bronze/silver/gold.
- [ ] Jupyter UI đăng nhập được bằng JUPYTER_TOKEN trong .env.
- [ ] Smoke test ghi `s3a://bronze/smoke-test/` thành công.

Khi toàn bộ checklist trên đều đạt, task BDANGR20-21 được xem là Done.

## 8. Đề xuất bước tiếp theo

- Đăng ký bảng Bronze vào catalog.
- Bổ sung metastore đầy đủ ở issue sau.
- Nối luồng Airflow cho Bronze -> Silver -> Gold.
