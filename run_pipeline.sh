#!/bin/bash

# Thiết lập Dừng script ngay nếu có lệnh bị lỗi
set -e

echo -e "\n==================================================="
echo "   OLIST E-COMMERCE LAKEHOUSE - END-TO-END DEMO"
echo "==================================================="

echo -e "\n>> STEP 1: Stopping existing services and cleaning volumes to ensure a fresh state..."
docker-compose down -v

echo -e "\n>> STEP 2: Checking and downloading raw dataset..."
DATA_FOLDER="data/raw/olist"
if [ ! -f "$DATA_FOLDER/olist_orders_dataset.csv" ]; then
    echo "Raw data not found. Downloading via cURL..."
    mkdir -p $DATA_FOLDER
    curl -L -o $DATA_FOLDER/brazilian-ecommerce.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
    
    if [ -f "$DATA_FOLDER/brazilian-ecommerce.zip" ]; then
        echo "Extracting dataset..."
        unzip -o $DATA_FOLDER/brazilian-ecommerce.zip -d $DATA_FOLDER
        rm $DATA_FOLDER/brazilian-ecommerce.zip
    else
        echo -e "\033[1;31mFailed to download data.\033[0m"
        exit 1
    fi
else
    echo "Raw data already exists. Skipping download."
fi

echo -e "\n>> STEP 3: Fetching required JAR files..."
# Script giả định đã có quyền thực thi (chmod +x)
bash scripts/fetch-jars.sh

echo -e "\n>> STEP 3: Starting Infrastructure via Docker Compose..."
docker-compose up -d

echo -e "\n>> STEP 4: Waiting for services to initialize (wait 45 seconds)..."
# Chờ cho Postgres, Hive Metastore, Minio, Airflow khởi động hoàn toàn
sleep 45

echo -e "\n>> STEP 5: Verifying MinIO Init..."
# init-minio container thường khởi chạy một lần và exit, nhưng hãy đảm bảo bucket đã sẵn sàng
echo "MinIO buckets should be created by the init-minio service."
sleep 10

echo -e "\n==================================================="
echo "       RUNNING LAKEHOUSE PIPELINE (SPARK)"
echo "==================================================="

echo -e "\n>> RUNNING [1/3]: Bronze Layer Ingestion (Raw to Bronze)..."
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/01_ingest_bronze.py"

echo -e "\n>> RUNNING [2/3]: Silver Layer Processing (Bronze to Silver)..."
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/02_process_silver.py"

echo -e "\n>> RUNNING [3/3]: Gold Layer Analytics (Silver to Gold)..."
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/03_analytics_gold.py"


echo -e "\n==================================================="
echo "          VALIDATION & QUERY PROOF"
echo "==================================================="

echo -e "\n>> Registering Tables in Metastore (if needed)..."
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/register_tables.py" || true

echo -e "\n>> Proving data existence in Lakehouse (Executing check_tables.py)..."
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/check_tables.py"

echo -e "\n==================================================="
echo "     DEMO PIPELINE COMPLETED SUCCESSFULLY"
echo "==================================================="
echo "Services are currently running at:"
echo " - Airflow Web UI: http://localhost:8080"
echo " - Superset Dashboard: http://localhost:8088"
echo " - MinIO Console: http://localhost:9001"
echo ""
echo "To shutdown the workspace, run: docker-compose down"
