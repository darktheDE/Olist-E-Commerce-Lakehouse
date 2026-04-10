# scripts/register_database.py
from superset import db
from superset.models.core import Database

database_name = "Olist Lakehouse (Spark)"
sqlalchemy_uri = "hive://olist-thrift-server:10000/default"

existing_db = db.session.query(Database).filter_by(database_name=database_name).first()

if existing_db:
    existing_db.sqlalchemy_uri = sqlalchemy_uri
    print(f"Updated {database_name}")
else:
    new_db = Database(database_name=database_name, sqlalchemy_uri=sqlalchemy_uri)
    db.session.add(new_db)
    print(f"Added {database_name}")

db.session.commit()
