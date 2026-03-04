# sqlAlchemy base(what alembic will read)

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

created_at = Column(
    DateTime,
    default=lambda: datetime.now(timezone.utc)
)

Base = declarative_base()

# user class allows us to explain on personalized listening history, and personalization
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="user")

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    genre = Column(String(100))

    tempo = Column(Float)
    key = Column(String(10))
    energy = Column(Float)

    interactions = relationship("Interaction", back_populates="track")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"),nullable=False)
    track_id =Column(Integer, ForeignKey("tracks.id"),nullable=False)

    action = Column(String(50)) # (like, skip, play)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    track = relationship("Track", back_populates="interactions")


