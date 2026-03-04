import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# If you aren't using python-dotenv, these can be set in your shell instead.
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "app_password")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "project_db")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # helps keep connections healthy
    pool_size=5,
    max_overflow=10, future=True,

)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
