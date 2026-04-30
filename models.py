# sqlAlchemy base(what alembic will read)

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime, JSON, UniqueConstraint,
    Boolean, Text, BigInteger, Numeric
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone


Base = declarative_base()

# user class allows us to explain on personalized listening history, and personalization
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)

    # Account fields
    username = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="user")
    blacklisted_tokens = relationship(
        "TokenBlacklist",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions = relationship("Session", back_populates="user")
    listening_history = relationship("ListeningHistory", back_populates="user", cascade ="all, delete-orphan")
    ratings = relationship("UserRating", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Genre(Base):
    __tablename__ = "genres"

    genre_id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("genres.genre_id"), nullable=True)

    parent = relationship("Genre", remote_side=[genre_id], backref="children")



class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    genre = Column(String(100))

    tempo = Column(Float)
    key = Column(String(10))
    energy = Column(Float)

    fma_track_id = Column(Integer, unique=True, nullable=True)

    interactions = relationship("Interaction", back_populates="track")
    audio_features = relationship(
        "AudioFeature",
        back_populates="track",
        uselist=False,
        cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "SongEmbedding",
        back_populates="track",
        cascade="all, delete-orphan"
    )
    outgoing_similarities = relationship(
        "SongSimilarity",
        foreign_keys="SongSimilarity.track_id",
        back_populates="track",
        cascade="all, delete-orphan"
    )
    incoming_similarities = relationship(
        "SongSimilarity",
        foreign_keys="SongSimilarity.similar_track_id",
        back_populates="similar_track",
        cascade="all, delete-orphan"
    )
    listening_history = relationship(
        "ListeningHistory",
        back_populates="track",
        cascade="all, delete-orphan"
    )
    ratings = relationship("UserRating",
                           back_populates="track",
                           cascade="all, delete-orphan")



class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"),nullable=False)
    track_id =Column(Integer, ForeignKey("tracks.id"),nullable=False)

    action = Column(String(50)) # (like, skip, play)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    track = relationship("Track", back_populates="interactions")

class AudioFeature(Base):
    __tablename__ = "audio_features"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False, unique=True)


    tempo = Column(Float, nullable=True)
    key = Column(String(10), nullable=True)
    energy = Column(Float, nullable=True)

    #  V3 features
    danceability = Column(Float, nullable=True)
    valence = Column(Float, nullable=True)
    acousticness = Column(Float, nullable=True)
    instrumentalness = Column(Float, nullable=True)
    speechiness = Column(Float, nullable=True)
    liveness = Column(Float, nullable=True)

    track = relationship("Track", back_populates="audio_features")

class SongEmbedding(Base):
    __tablename__ = "song_embeddings"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)


    model_name = Column(String(50), nullable=False, default="clap")
    model_version = Column(String(50), nullable=False, default="v3")


    vector = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    track = relationship("Track", back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint("track_id", "model_version", name="uq_song_embeddings_track_version"),
    )


class SongSimilarity(Base):
    __tablename__ = "song_similarities"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    similar_track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)

    similarity_score = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False, default="v3")
    created_at = Column(DateTime, default=datetime.utcnow)

    track = relationship(
        "Track",
        foreign_keys=[track_id],
        back_populates="outgoing_similarities"
    )
    similar_track = relationship(
        "Track",
        foreign_keys=[similar_track_id],
        back_populates="incoming_similarities"
    )

    __table_args__ = (
        UniqueConstraint(
            "track_id",
            "similar_track_id",
            "model_version",
            name="uq_song_similarities_pair_version"
        ),
    )


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_jti = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="blacklisted_tokens")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    favorite_genres = Column(JSON, nullable=True)
    preferred_decades = Column(JSON, nullable=True)
    mood_preferences = Column(JSON, nullable=True)
    explicit_content_filter = Column(Boolean, default=False)
    recommendation_diversity = Column(Numeric(2, 1), default=0.5)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    taste_vector = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan")


class SessionEvent(Base):
    __tablename__ = "session_events"

    id = Column(BigInteger, primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=True)

    event_type = Column(String(50), nullable=False)  # play, like, skip, playlist_add, reset
    context = Column(String(50), nullable=True)
    completion_rate = Column(Numeric(3, 2), nullable=True)
    latency_ms = Column(Integer, nullable=True)

    occurred_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="events")


class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)

    played_at = Column(DateTime, default=datetime.utcnow)
    duration_played_seconds = Column(Integer, nullable=True)
    completion_rate = Column(Numeric(3, 2), nullable=True)
    context = Column(String(50), nullable=True)

    user = relationship("User", back_populates="listening_history")
    track = relationship("Track", back_populates="listening_history")


class UserRating(Base):
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)

    rating = Column(Integer, nullable=True)  # 1-5
    is_favorite = Column(Boolean, default=False)
    is_disliked = Column(Boolean, default=False)
    rated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")
    track = relationship("Track", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_user_ratings_user_track"),
    )