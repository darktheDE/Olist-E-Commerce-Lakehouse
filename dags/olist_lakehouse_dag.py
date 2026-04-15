from __future__ import annotations

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'olist-lakehouse',
    'depends_on_past': False,
    'email_notification': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'olist_lakehouse_pipeline',
    default_args=default_args,
    description='Orchestrate Olist Lakehouse pipeline: Bronze -> Silver -> Gold',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['lakehouse', 'olist'],
) as dag:

    ingest_bronze = BashOperator(
        task_id='ingest_bronze',
        bash_command='python /opt/airflow/jobs/01_ingest_bronze.py',
    )

    register_tables = BashOperator(
        task_id='register_tables',
        bash_command='python /opt/airflow/jobs/register_tables.py',
    )

    check_tables = BashOperator(
        task_id='check_tables',
        bash_command='python /opt/airflow/jobs/check_tables.py',
    )

    process_silver = BashOperator(
        task_id='process_silver',
        bash_command='python /opt/airflow/jobs/02_process_silver.py',
    )

    analytics_gold = BashOperator(
        task_id='analytics_gold',
        bash_command='python /opt/airflow/jobs/03_analytics_gold.py',
    )

    ingest_bronze >> register_tables >> check_tables >> process_silver >> analytics_gold
