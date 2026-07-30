# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local-Docker **Data Lakehouse** built on the Brazilian Olist E-Commerce public dataset, implementing the **Medallion Architecture** (Bronze → Silver → Gold) with Delta Lake on MinIO (S3-compatible storage), a PostgreSQL-backed Hive Metastore, Apache Spark for transforms, Apache Airflow for orchestration, and Apache Superset (via Spark Thrift Server) for BI.

## Architecture (Big Picture)

```
CSVs (data/raw/olist)
        │
        ▼
[01_ingest_bronze.py]  ──► s3a://bronze/olist_*     (raw → Delta, inferSchema)
        │
        ▼
[register_tables.py]    ──► Hive Metastore (Postgres) CREATE TABLE ... USING DELTA LOCATION
        │
        ▼
[02_process_silver.py]  ──► s3a://silver/denormalized_sales  +  Hive default.silver_sales
        │                  (drop canceled, coalesce timestamps, denormalize joins)
        ▼
[03_analytics_gold.py]  ──► s3a://gold/rfm_segments           +  Hive default.gold_rfm_segments
                           (RFM scoring via ntile windows, partitioned by rfm_segment)
        │
        ▼
Superset ◄── Thrift Server (hive://olist-thrift-server:10000/default)
```

**Key contracts that hold the system together:**
- All Delta tables are registered in the `default` Hive database via `CREATE TABLE IF NOT EXISTS … USING DELTA LOCATION …` so they're queryable through the Thrift Server.
- MinIO is treated as S3 via the `s3a://` protocol (`MINIO_ENDPOINT=http://minio:9000` from inside containers; `localhost:9000` from host).
- Every job script is **standalone runnable** — it adds `PROJECT_ROOT` to `sys.path`, builds its own Spark session via `src.spark_session.get_spark_session()`, and stops it in a `finally` block.

## Common Commands

### Bring up the full stack
```bash
# One-shot demo (cleans volumes, downloads dataset, fetches jars, runs pipeline):
./run_pipeline.sh          # Linux/Mac/Git Bash
pwsh ./run_pipeline.ps1     # Windows PowerShell

# Or manually:
docker compose up -d
```

### Run individual pipeline stages
```bash
# Inside the Airflow scheduler container (jobs are mounted at /opt/airflow/jobs):
docker compose exec airflow-scheduler python /opt/airflow/jobs/01_ingest_bronze.py
docker compose exec airflow-scheduler python /opt/airflow/jobs/register_tables.py
docker compose exec airflow-scheduler python /opt/airflow/jobs/02_process_silver.py
docker compose exec airflow-scheduler python /opt/airflow/jobs/03_analytics_gold.py
docker compose exec airflow-scheduler python /opt/airflow/jobs/check_tables.py
```

### Local Python (`.venv`) — bypass Docker for debugging
```bash
python -m venv .venv
source .venv/bin/activate   # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
python jobs/01_ingest_bronze.py
```
The local `.venv` reaches MinIO/Postgres through the exposed host ports (configured in `src/config.py` defaults).

### Service endpoints (after `docker compose up -d`)
| Service | URL | Credentials |
|---|---|---|
| Airflow Webserver | http://localhost:8080 | `admin` / `admin` |
| Superset | http://localhost:8088 | `admin` / `admin` |
| MinIO Console | http://localhost:9001 | `minioadmin` / `minioadmin` |
| Spark Thrift Server | `hive://localhost:10000/default` | — |
| Postgres (Hive metastore + Airflow DB) | `localhost:5432` | `metastore` / `metastore123`, DBs `metastore` + `airflow` |

### Trigger the DAG
Open the Airflow UI → unpause `olist_lakehouse_pipeline` → trigger. Tasks: `ingest_bronze` → `register_tables` → `check_tables` → `process_silver` → `analytics_gold`.

### Import a pre-built Superset dashboard
```powershell
docker cp docs/dashboard_export.zip olist-superset:/tmp/dashboard.zip
docker exec -it olist-superset bash -c "superset import-dashboards -p /tmp/dashboard.zip -u admin"
```

### Teardown
```bash
docker compose down       # keep volumes
docker compose down -v    # wipe MinIO, Postgres, Superset state
```

## Key Files & Directories

- **`dags/olist_lakehouse_dag.py`** — Thin Airflow DAG wiring the five jobs via `BashOperator`. Schedule is `None` (manual trigger).
- **`jobs/`** — Idempotent PySpark ETL scripts. Each has a `main()` that builds a Spark session, executes, and stops in `finally`. Naming convention: `NN_stage.py`.
- **`src/config.py`** — All environment-driven configuration: MinIO endpoints/keys, bucket names, Postgres connection, Spark package versions, and the **`CSV_DATASETS`** dict that drives Bronze ingestion. Add new datasets by extending this dict.
- **`src/spark_session.py`** — The single `get_spark_session(app_name)` factory. Wires Delta extensions, S3A→MinIO configs, and Hive Metastore JDBC. Reuse this for any new Spark job.
- **`conf/spark-defaults.conf`** — Spark config used by the Thrift Server container (mounted read-only into `/opt/spark/conf/`).
- **`scripts/`** — One-shot init: `init-minio.sh` creates the three buckets; `setup-superset.sh` + `register_database.py` add the Thrift-backed DB to Superset; `hive-schema-2.3.0.postgres.sql` initializes the metastore schema; `init-airflow-db.sql` provisions the `airflow` DB + user.
- **`jars/`** — Vendored JARs (Delta, hadoop-aws, postgresql JDBC, etc.) mounted into both Airflow and the Thrift Server. Run `bash scripts/fetch-jars.sh` if any are missing.
- **`notebooks/`** — `.ipynb` files (Hive check, silver check, RFM verify) for VS Code / Jupyter exploration against the running stack.
- **`Dockerfile.airflow`** — Airflow image base with Java + the postgres JDBC jar + `pyspark==3.5.8` + `delta-spark==3.1.0`.
- **`.env.example`** — Template for `.env` (MinIO creds, Postgres creds, Superset creds, secret key). The compose file reads `.env` directly.
- **`docs/`** — Architecture diagram (`SYSARCH_OLIST.jpg`), dashboard screenshot, and `dashboard_export.zip`.

## Conventions & Gotchas

- **Bronze vs. Silver path names**: Bronze uses `s3a://bronze/olist_<dataset>` (one Delta table per source CSV); Silver/Gold use plain `s3a://silver/<name>` / `s3a://gold/<name>`. The helpers `get_bronze_table_path`, `get_silver_table_path`, `get_gold_table_path` in `src/config.py` enforce this.
- **Reference date for RFM**: `03_analytics_gold.py` does **not** use `current_date()` — it derives the reference date from `MAX(order_purchase_timestamp)` in the dataset, since Olist data is historical. Change this only with intent.
- **`.env` is gitignored but compose relies on it.** Copy `.env.example` → `.env` before first `docker compose up`.
- **The `airflow-common` YAML anchor** in `docker-compose.yml` is shared by webserver, scheduler, and init. Any change to `PYSPARK_SUBMIT_ARGS`, mounts, or env applies to all three.
- **ER-01 flags**: `spark.hadoop.datanucleus.schema.autoCreateAll=false` and `spark.hadoop.hive.metastore.schema.verification=false` are set because the Hive metastore schema is bootstrapped by the SQL files in `scripts/` rather than auto-created.
- **No `.env` file = services fail to start.** `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` and `POSTGRES_*` are required.
- **Airflow DAGs are paused on creation** (`AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'`) — you must unpause in the UI.
- **`POSTGRES_DB`/`USER`/`PASSWORD`** in `.env` apply to the *metastore* database, while `airflow` DB credentials are hardcoded in the DAG-side `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` and `init-airflow-db.sql`. Don't confuse the two.