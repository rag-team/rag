import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

MYSQL_USER = os.environ.get("MYSQL_USER", "mysql")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "password")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysqlDB")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_DB_NAME = os.environ.get("MYSQL_DB_NAME", "schlagwortdb")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
