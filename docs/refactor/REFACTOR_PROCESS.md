# REFACTOR PROCESS — Olist E-Commerce Lakehouse

> **Nguyên tắc vận hành:** Mỗi mục được lên kế hoạch → chờ duyệt → triển khai → manual test → pass → mới đi tiếp mục kế.
> Mọi thay đổi đều được ghi lại trong file này theo từng mục.

---

## MỤC LỤC REFACTOR

| # | Mục | Vấn đề cốt lõi | Mức độ ưu tiên |
|---|-----|----------------|----------------|
| **RF-01** | [Sửa lỗi Hive Metastore khởi động lần đầu](#rf-01) | `MissingTableException` do schema chưa được init trước khi Spark kết nối | 🔴 Critical |
| **RF-02** | [Sửa lỗi Airflow DB init (relation "log" does not exist)](#rf-02) | PostgreSQL chỉ có 1 database `metastore`; Airflow cần schema riêng `airflow` nhưng chưa được init đúng thứ tự | 🔴 Critical |
| **RF-03** | [Loại bỏ lỗi "2 tasks chạy cùng lúc" trên Airflow](#rf-03) | DAG có `schedule_interval=timedelta(days=1)` + `start_date=2024-01-01` → Airflow backfill và chạy task mới song song | 🟠 High |
| **RF-04** | [Chuẩn hóa JAR loading — ưu tiên local, fallback download](#rf-04) | Mỗi lần chạy Spark đều download JAR từ Maven (chậm, dễ timeout 0-byte). JARs local đã có nhưng chưa được dùng đúng cách trong Airflow | 🟠 High |
| **RF-05** | [Nâng cấp image Spark 3.5.0 → 3.5.5 (hoặc 3.5.x stable)](#rf-05) | `apache/spark:3.5.0` không còn được Docker Hub list chính thức; nhiều bug đã được fix ở 3.5.x mới hơn | 🟡 Medium |
| **RF-06** | [Quyết định số phận container pyspark-notebook](#rf-06) | Nếu pipeline chạy qua Airflow, Jupyter notebook trùng lặp tài nguyên; cần giữ lại hay tách profile | 🟡 Medium |
| **RF-07** | [Tối ưu spark.master — chuyển sang local[2] hoặc giữ local[*]](#rf-07) | `local[*]` dùng toàn bộ CPU cores, cạnh tranh tài nguyên với các container khác | 🟢 Low |

---

## PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE ANALYSIS)

### Vấn đề 1 — Hive Metastore MissingTableException

**Triệu chứng:** Lần đầu chạy `docker compose up`, container `olist-thrift-server` (và mọi Spark job gọi Hive) báo lỗi:
```
MissingTableException: Required table missing: "DBS", "CDS", "VERSION"
```

**Root cause:**
Spark được config `spark.hadoop.javax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/metastore`.
Điều này có nghĩa **Spark dùng PostgreSQL làm backend Hive Metastore**.
Khi Spark kết nối lần đầu, nó kiểm tra xem schema Hive (bảng `DBS`, `CDS`, `VERSION`, v.v.) đã tồn tại chưa.
Thực tế, database `metastore` trên PostgreSQL **chỉ là database trống** — chưa có bảng nào.

Spark có 2 options:
- `datanucleus.schema.autoCreateAll=true` → tự tạo schema (phù hợp lần đầu)
- `hive.metastore.schema.verification=false` → bỏ qua kiểm tra version

Trong `spark-defaults.conf` hiện tại: `autoCreateAll=false` + `verification=true` → Spark **từ chối kết nối** vì thấy thiếu bảng nhưng cũng không tự tạo.
Trong `spark_session.py` hiện tại: `autoCreateAll=false` + `verification=false` → có thể tạm thời bỏ qua, nhưng **vẫn không có bảng Hive**, nên sau này register_tables sẽ lỗi hoặc metadata bị sai.

**Giải pháp đúng:** Phải chạy `schematool -dbType postgres -initSchema` **một lần duy nhất trước khi** Spark kết nối. Đây là tool chuẩn của Apache Hive để tạo schema cơ sở trên PostgreSQL.

### Vấn đề 2 — Airflow DB (relation "log" does not exist)

**Triệu chứng:** PostgreSQL log:
```
ERROR: relation "log" does not exist at character 13
STATEMENT: INSERT INTO log (dttm, event, ...) ...
```

**Root cause:**
`init-airflow-db.sql` tạo database `airflow` và user `airflow`, nhưng **không chạy `airflow db init`** để tạo các bảng Airflow (`log`, `dag`, `task_instance`, v.v.). Script SQL này chỉ là DDL bootstrap — Airflow cần tự khởi tạo schema qua lệnh `airflow db init`.

Trong `docker-compose.yml`, service `airflow-init` có lệnh `airflow db init` nhưng container này **không có `depends_on` đảm bảo chạy trước** `airflow-webserver` và `airflow-scheduler`. Nếu 3 container này race condition, webserver/scheduler có thể cố kết nối DB trong khi `airflow-init` chưa xong.

### Vấn đề 3 — 2 Tasks chạy cùng lúc

**Triệu chứng:** Bấm Trigger nhưng thấy 2 tasks chạy.

**Root cause:**
DAG có `schedule_interval=timedelta(days=1)` và `start_date=datetime(2024, 1, 1)`.
Airflow Scheduler khi khởi động sẽ kiểm tra: "Từ 2024-01-01 đến nay đã cần chạy bao nhiêu lần?"
Dù có `catchup=False`, **Airflow vẫn có thể tạo 1 scheduled run gần nhất**. Khi user bấm Trigger thủ công thêm 1 run, tổng thành 2 runs chạy song song.

**Giải pháp:** Đặt `schedule_interval=None` → DAG hoàn toàn manual-only.


## RF-03 — Loại bỏ lỗi "2 tasks chạy cùng lúc"

> **Trạng thái:** ⬜ Chờ lên kế hoạch

*(Sẽ được lên kế hoạch chi tiết sau khi RF-01 pass)*

**Tóm tắt:** Đổi `schedule_interval=None` trong DAG. Xem xét tách 1 DAG chính thành 5 DAG riêng biệt theo từng task để dễ debug từng bước.

---

## RF-04 — Chuẩn hóa JAR loading

> **Trạng thái:** ⬜ Chờ RF-01 pass

*(Sẽ được lên kế hoạch chi tiết sau khi RF-01 pass)*

**Tóm tắt:** Loại bỏ `--packages` trong `PYSPARK_SUBMIT_ARGS` (tức là không download từ Maven mỗi lần chạy). Thay vào đó dùng `--jars /opt/airflow/jars/*` với toàn bộ JARs đã có sẵn trong thư mục `jars/`. JARs đã có: delta-spark, delta-storage, hadoop-aws, aws-java-sdk-bundle (267MB), antlr4, wildfly-openssl, postgresql. Tất cả đủ để Spark chạy offline.

---

## RF-05 — Nâng cấp image Spark

> **Trạng thái:** ⬜ Chờ RF-04 pass

*(Sẽ được lên kế hoạch chi tiết sau khi RF-04 pass)*

---

## RF-06 — Quyết định số phận pyspark-notebook

> **Trạng thái:** ⬜ Chờ RF-05 pass

*(Sẽ được lên kế hoạch chi tiết sau khi RF-05 pass)*

---

## RF-07 — Tối ưu spark.master

> **Trạng thái:** ⬜ Chờ RF-06 pass

*(Sẽ được lên kế hoạch chi tiết sau khi RF-06 pass)*

---

## CHANGELOG

| Ngày | Mục | Status | Ghi chú |
|------|-----|--------|---------|
| 2026-04-15 | RF-01 | 🟡 Chờ manual test | Đã triển khai xong; chờ bạn chạy test |