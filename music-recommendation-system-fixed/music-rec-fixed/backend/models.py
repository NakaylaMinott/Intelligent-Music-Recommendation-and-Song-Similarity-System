"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class User(Base):
    """User model for storing user information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Track(Base):
    """Track model for storing music track information"""
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    artist = Column(String(255), nullable=False, index=True)
    album = Column(String(255), nullable=True)
    genre = Column(String(100), index=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Audio features for similarity computation
    tempo = Column(Float, nullable=True)  # BPM
    key = Column(String(10), nullable=True)  # Musical key
    energy = Column(Float, nullable=True)  # 0.0 to 1.0
    danceability = Column(Float, nullable=True)  # 0.0 to 1.0
    valence = Column(Float, nullable=True)  # Musical positiveness 0.0 to 1.0
    acousticness = Column(Float, nullable=True)  # 0.0 to 1.0
    instrumentalness = Column(Float, nullable=True)  # 0.0 to 1.0
    loudness = Column(Float, nullable=True)  # dB
    speechiness = Column(Float, nullable=True)  # 0.0 to 1.0
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    interactions = relationship("Interaction", back_populates="track", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_artist_genre', 'artist', 'genre'),
    )

    def __repr__(self):
        return f"<Track(id={self.id}, title='{self.title}', artist='{self.artist}')>"


class Interaction(Base):
    """Interaction model for tracking user-track interactions"""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False, index=True)
    
    action = Column(String(50), nullable=False)  # play, like, skip, playlist_add
    rating = Column(Integer, nullable=True)  # Optional rating 1-5
    listen_duration = Column(Integer, nullable=True)  # Seconds listened
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="interactions")
    track = relationship("Track", back_populates="interactions")

    # Composite index for queries
    __table_args__ = (
        Index('idx_user_track', 'user_id', 'track_id'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Interaction(user_id={self.user_id}, track_id={self.track_id}, action='{self.action}')>"
