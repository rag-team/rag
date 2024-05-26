from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

USER = "mysql"
PASSWORD = "password"
MYSQL_HOST = "mysqlDB"
MYSQL_PORT = "3306"
MYSQL_DB_NAME = "schlagwortdb"

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
