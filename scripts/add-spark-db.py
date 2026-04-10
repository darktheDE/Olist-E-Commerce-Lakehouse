# scripts/add-spark-db.py
import os
from superset import db
from superset.models.core import Database

def add_spark_db():
    database_name = "Olist Lakehouse (Spark)"
    sqlalchemy_uri = "hive://olist-thrift-server:10000/default"
    
    print(f"Checking for existing database: {database_name}")
    existing_db = db.session.query(Database).filter_by(database_name=database_name).first()
    if existing_db:
        print(f"Database {database_name} already exists. Updating URI...")
        existing_db.sqlalchemy_uri = sqlalchemy_uri
    else:
        print(f"Creating new database: {database_name}")
        new_db = Database(
            database_name=database_name,
            sqlalchemy_uri=sqlalchemy_uri,
        )
        db.session.add(new_db)
    
    db.session.commit()
    print(f"[SUCCESS] Database {database_name} is configured in Superset.")

if __name__ == "__main__":
    add_spark_db()
