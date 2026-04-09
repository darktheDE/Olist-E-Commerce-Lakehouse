# 🛒 Olist E-Commerce Data Lakehouse

![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C.svg?style=for-the-badge&logo=Apache-Spark&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-C7202C.svg?style=for-the-badge&logo=MinIO&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta%20Lake-00A9E0.svg?style=for-the-badge)
![Apache Hive](https://img.shields.io/badge/Hive_Metastore-FDEE21.svg?style=for-the-badge&logo=apachehive&logoColor=black)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE.svg?style=for-the-badge&logo=Apache-Airflow&logoColor=white)
![Apache Superset](https://img.shields.io/badge/Apache%20Superset-00A699.svg?style=for-the-badge&logo=apache&logoColor=white)

> **Academic Project - Big Data Analysis Course**  
> **Institution:** Ho Chi Minh City University of Technology and Engineering (HCM-UTE)  
> **Group:** 22 

## 📑 Table of Contents
- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Medallion Data Pipeline](#-medallion-data-pipeline)
- [Tech Stack](#-tech-stack)
- [Prerequisites & Setup](#-prerequisites--setup)
- [Project Structure](#-project-structure)
- [Team Members & Contributions](#-team-members--contributions)

## 📖 Project Overview
This project focuses on building a complete, end-to-end **Data Lakehouse** pipeline to process, manage, and analyze massive volumes of e-commerce data. Utilizing the Brazilian E-Commerce Public Dataset by Olist (Kaggle), the system is designed to extract actionable business insights such as **RFM (Recency, Frequency, Monetary) Customer Segmentation**, delivery KPIs, and sales trends.

The project strictly adheres to the modern 5-layer Data Lakehouse architecture, leveraging distributed processing engines (Apache Spark) and ACID-compliant storage (Delta Lake) over legacy big data tools.

## 🏗️ System Architecture
The system architecture implements the core five layers of a Data Lakehouse:

1. **Ingestion Layer:** Batch processing of raw CSV files.
2. **Storage Layer:** Object storage via **MinIO** (S3-compatible) utilizing the **Delta Lake** format to guarantee ACID properties.
3. **Metadata Layer:** Centralized Data Catalog powered by **Hive Metastore** (backed by **PostgreSQL**) to define schema and manage data access.
4. **Processing / API Layer:** Data transformations, joins, and aggregations executed via **Apache Spark** (DataFrame API & Spark SQL).
5. **Consumption Layer:** Interactive BI dashboards built with **Apache Superset**.
6. **Orchestration:** End-to-end pipeline automation scheduled via **Apache Airflow**.

```mermaid
flowchart LR
    Source[/"📁 Olist Dataset (CSV)"/]
    User(("👨‍💼 Business Analysts"))

    subgraph Data Lakehouse Architecture
        L1["Ingestion (Spark Batch)"]
        L2["Storage (MinIO + Delta Lake)"]
        L3["Metadata (Hive Metastore + PostgreSQL)"]
        L4["Processing (Apache Spark)"]
        L5["Consumption (Superset)"]
    end

    Airflow["🌀 Apache Airflow (Orchestration)"]

    Source -->|Read| L1
    L1 -->|Write Bronze| L2
    L2 <-->|Read/Write Silver & Gold| L4
    L3 -. "Schema Provider" .- L4
    L3 -. "Schema Provider" .- L5
    L4 -->|Aggregated Data| L5
    L5 -->|Dashboards| User
    Airflow -. "Schedules Pipeline" .- L1
    Airflow -. "Schedules Pipeline" .- L4
```

## 🏅 Medallion Data Pipeline

The data lifecycle is managed using the Medallion Architecture:

### 🥉 Bronze Layer (Raw Data)
Ingests raw CSV data from the Olist dataset and saves it in Delta format without schema enforcement.

### 🥈 Silver Layer (Cleansed & Conformed)
Filters out canceled orders, handles missing values, casts data types (e.g., Timestamps), and performs distributed joins across multiple tables (orders, customers, products, order_items) to create denormalized factual tables.

### 🥇 Gold Layer (Aggregated Analytics)
Applies advanced Spark SQL window functions and aggregations to generate business-ready tables:

- **gold_rfm_segments**: Customer segmentation based on RFM scores.
- **gold_delivery_kpis**: Logistics performance tracking.
- **gold_sales_trends**: Revenue generation over time.

## 🛠️ Tech Stack
| Component | Technology | Description |
| :--- | :--- | :--- |
| Storage Engine | MinIO | S3-Compatible object storage for local environments. |
| Table Format | Delta Lake | Brings ACID transactions to Apache Spark and big data workloads. |
| Processing Engine| PySpark & Spark SQL | In-memory distributed computing framework. |
| Data Catalog | Hive Metastore | Manages metadata schemas. |
| RDBMS (Backend) | PostgreSQL | Acts as the backing database for Hive Metastore. |
| Orchestration | Apache Airflow | Automates data pipelines (DAGs). |
| Visualization | Apache Superset | Open-source modern data exploration and BI platform. |
| Infrastructure | Docker Compose | Containerization for reproducible environments. |
## 🚀 Prerequisites & Setup
### 1. Prerequisites

Ensure you have the following installed on your machine:
- Docker & Docker Compose
- Git

### 2. Installation

Clone the repository to your local machine:
```bash
git clone https://github.com/your-repo/olist-data-lakehouse.git
cd olist-data-lakehouse
```

### 3. Spin up the Infrastructure

Start the entire Data Lakehouse stack using Docker Compose:

```bash
docker-compose up -d
```

Wait approximately 2-3 minutes for all containers (Spark, MinIO, Hive, PostgreSQL, Airflow, Superset) to initialize.

### 4. Service Endpoints

Once the containers are running, access the services via:

MinIO Console: http://localhost:9001 (Default: minioadmin / minioadmin)

Airflow Web UI: http://localhost:8080 (Default: airflow / airflow)

Superset: http://localhost:8088 (Default: admin / admin)

Spark UI: http://localhost:4040 (Available during job execution)

### 5. Running the Pipeline

Trigger the DAG named olist_medallion_pipeline in the Airflow UI, or run the Spark jobs manually:

```bash
docker exec -it spark-master spark-submit /opt/workspace/jobs/01_ingest_bronze.py
docker exec -it spark-master spark-submit /opt/workspace/jobs/02_process_silver.py
docker exec -it spark-master spark-submit /opt/workspace/jobs/03_analytics_gold.py
```

## 📁 Project Structure
```text
.
├── dags/                       # Apache Airflow DAGs
│   └── olist_pipeline_dag.py
├── data/                       # Local volume mapping for raw CSVs (Ignored by Git)
├── jobs/                       # PySpark scripts for ETL
│   ├── 01_ingest_bronze.py
│   ├── 02_process_silver.py
│   └── 03_analytics_gold.py
├── notebooks/                  # Jupyter notebooks for Data Exploration and PoC
│   └── 00_spike_test.ipynb
├── src/                        # Shared utility modules for PySpark jobs
│   ├── __init__.py
│   ├── spark_session.py        # Centralized SparkSession builder with MinIO config
│   └── config.py               # Constants, table names, S3 paths
├── conf/                       # Configuration files (Spark defaults, Hive-site)
│   └── spark-defaults.conf
├── docker-compose.yml          # Infrastructure setup
├── requirements.txt            # Python dependencies
├── .gitignore                  # Exclude raw data and logs
└── README.md                   # Project documentation
```

## 👥 Team Members & Contributions
| Name | Student ID | Primary Role | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| Đinh Trọng Đức Anh | 22110096 | Infrastructure & Bronze Layer | Docker setup, MinIO configuration, Data Ingestion (CSV to Delta). |
| Lê Văn Lộc | 22110178 | Silver Layer (ETL) | Big Data transformations, data cleansing, distributed joins using PySpark. |
| Nguyễn An Khang | 22110190 | Gold Layer (Analytics) | Advanced Spark SQL, analytical functions, RFM computation, KPIs. |
| Vũ Kiều Thúy Vân | 22110266 | Governance & Consumption | Hive Metastore cataloging, Airflow Orchestration, Superset Dashboards. |

Developed for the Big Data Analysis Course - Spring Semester 2026-2027.
