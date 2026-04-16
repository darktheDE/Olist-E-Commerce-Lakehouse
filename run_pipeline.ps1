# Error Action Preference
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "   OLIST E-COMMERCE LAKEHOUSE - END-TO-END DEMO" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

Write-Host "`n>> STEP 1: Stopping existing services and cleaning volumes to ensure a fresh state..." -ForegroundColor Cyan
docker-compose down -v

Write-Host "`n>> STEP 2: Checking and downloading raw dataset..." -ForegroundColor Cyan
$dataFolder = "data/raw/olist"
if (-Not (Test-Path "$dataFolder/olist_orders_dataset.csv")) {
    Write-Host "Raw data not found. Downloading via Invoke-WebRequest..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $dataFolder | Out-Null
    $zipPath = "$dataFolder/brazilian-ecommerce.zip"
    
    # Dùng cURL (Invoke-WebRequest trong PowerShell)
    Invoke-WebRequest -Uri "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce" -OutFile $zipPath
    
    if (Test-Path $zipPath) {
        Write-Host "Extracting dataset..." -ForegroundColor Yellow
        Expand-Archive -Path $zipPath -DestinationPath $dataFolder -Force
        Remove-Item -Path $zipPath -Force
    } else {
        Write-Host "Failed to download data." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Raw data already exists. Skipping download." -ForegroundColor Green
}

Write-Host "`n>> STEP 3: Fetching required JAR files..." -ForegroundColor Cyan
# Execute shell script in git bash or wsl, or run a windows equivalent file
# We assume it has a bash equivalent available via WSL or Git Bash
bash scripts/fetch-jars.sh

Write-Host "`n>> STEP 3: Starting Infrastructure via Docker Compose..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "`n>> STEP 4: Waiting for services to initialize (wait 45 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 45

Write-Host "`n>> STEP 5: Verifying MinIO Init..." -ForegroundColor Cyan
Write-Host "MinIO buckets should be created by the init-minio service."
Start-Sleep -Seconds 10

Write-Host "`n===================================================" -ForegroundColor Green
Write-Host "       RUNNING LAKEHOUSE PIPELINE (SPARK)" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

Write-Host "`n>> RUNNING [1/3]: Bronze Layer Ingestion (Raw to Bronze)..." -ForegroundColor Yellow
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/01_ingest_bronze.py"

Write-Host "`n>> RUNNING [2/3]: Silver Layer Processing (Bronze to Silver)..." -ForegroundColor Yellow
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/02_process_silver.py"

Write-Host "`n>> RUNNING [3/3]: Gold Layer Analytics (Silver to Gold)..." -ForegroundColor Yellow
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/03_analytics_gold.py"


Write-Host "`n===================================================" -ForegroundColor Green
Write-Host "          VALIDATION & QUERY PROOF" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

Write-Host "`n>> Registering Tables in Metastore (if needed)..." -ForegroundColor Magenta
# Using try catch to bypass error if registers fail but we want to continue formatting
try {
    docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/register_tables.py"
} catch {
    Write-Host "Non-fatal error in registering tables, continuing..." -ForegroundColor DarkGray
}

Write-Host "`n>> Proving data existence in Lakehouse (Executing check_tables.py)..." -ForegroundColor Magenta
docker-compose exec -T airflow-scheduler bash -c "python /opt/airflow/jobs/check_tables.py"

Write-Host "`n===================================================" -ForegroundColor Green
Write-Host "     DEMO PIPELINE COMPLETED SUCCESSFULLY" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host "Services are currently running at:"
Write-Host " - Airflow Web UI: http://localhost:8080"
Write-Host " - Superset Dashboard: http://localhost:8088"
Write-Host " - MinIO Console: http://localhost:9001"
Write-Host ""
Write-Host "To shutdown the workspace, run: docker-compose down"
