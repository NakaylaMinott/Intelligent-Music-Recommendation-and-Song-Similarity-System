"""
Database configuration — wraps db.py with a FastAPI-compatible get_db() dependency.

db.py and models.py are sibling files in the same backend/ directory.
"""
from typing import Generator

from db import engine, SessionLocal          # db.py in same folder
from models import Base                       # models.py in same folder


def get_db() -> Generator:
    """
    FastAPI dependency — yields a SQLAlchemy session and cleans up on exit.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
