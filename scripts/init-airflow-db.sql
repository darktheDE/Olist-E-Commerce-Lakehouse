-- Create Airflow database and user if they don't exist
-- Note: This script is intended to be run by the 'postgres' user
CREATE DATABASE airflow;
CREATE USER airflow WITH PASSWORD 'airflow123';
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
ALTER DATABASE airflow OWNER TO airflow;
