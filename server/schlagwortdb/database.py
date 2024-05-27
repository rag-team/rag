import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

default_db = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "database", "schlagwortdb.sqlite"
)

SQLITE_DB = os.environ.get("SQLITE_DB", default_db)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create database if it doesn't exist
with engine.connect() as conn:
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
