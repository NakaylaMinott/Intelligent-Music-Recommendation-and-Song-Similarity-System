"""
Database configuration and session management
Using SQLite for easy local development (no DB server required)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# SQLite database - stored as a local file, no server needed
# To use MySQL instead, set: DATABASE_URL=mysql+pymysql://user:pass@host/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./music_recommendation.db")

# Create SQLAlchemy engine
# check_same_thread=False is required for SQLite with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency function to get database session
    Yields a database session and ensures proper cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
