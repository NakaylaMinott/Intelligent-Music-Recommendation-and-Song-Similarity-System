"""
Pydantic schemas for request/response validation

Corrected: TrackResponse and TrackCreate match the columns actually
present on db.models.Track (id, title, artist, genre, tempo, key, energy,
fma_track_id).  Extra audio features live in AudioFeature, not Track.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ==================== User Schemas ====================
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    username: Optional[str] = None


class UserResponse(UserBase):
    id: int
    username: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Track Schemas ====================
class TrackBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)


class TrackCreate(TrackBase):
    """Create a track — only columns that exist on the Track model."""
    tempo: Optional[float] = Field(None, ge=0, le=300)
    key: Optional[str] = Field(None, max_length=10)
    energy: Optional[float] = Field(None, ge=0, le=1)
    fma_track_id: Optional[int] = None


class TrackResponse(BaseModel):
    """Response schema matching Track model columns."""
    id: int
    title: str
    artist: str
    genre: Optional[str] = None
    tempo: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    fma_track_id: Optional[int] = None

    class Config:
        from_attributes = True


# ==================== Interaction Schemas ====================
class InteractionBase(BaseModel):
    user_id: int
    track_id: int
    action: str = Field(..., pattern="^(play|like|skip|playlist_add|dislike)$")


class InteractionCreate(InteractionBase):
    pass


class InteractionResponse(InteractionBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Recommendation Schemas ====================
class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    track_id: Optional[int] = None
    limit: int = Field(10, ge=1, le=50)
    genre: Optional[str] = None


class RecommendationResponse(BaseModel):
    track_id: int
    title: str
    artist: str
    genre: Optional[str] = None
    similarity_score: float = Field(..., ge=0, le=1)
    reason: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Statistics Schemas ====================
class TrackStatistics(BaseModel):
    track_id: int
    play_count: int
    like_count: int
    skip_count: int
    average_rating: Optional[float] = None


class UserStatistics(BaseModel):
    user_id: int
    total_interactions: int
    favorite_genre: Optional[str] = None
    total_listening_time: Optional[int] = None


# ==================== Bulk Operations ====================
class BulkTrackCreate(BaseModel):
    tracks: List[TrackCreate]

    @field_validator("tracks")
    @classmethod
    def validate_tracks_count(cls, v):
        if len(v) > 100:
            raise ValueError("Cannot create more than 100 tracks at once")
        return v


# ==================== Playlist schemas ====================
class PlaylistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PlaylistTrackItem(BaseModel):
    id: int
    title: str
    artist: str
    genre: Optional[str] = None
    energy: Optional[float] = None
    fma_track_id: Optional[int] = None

    class Config:
        from_attributes = True


class PlaylistResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    track_count: int = 0

    class Config:
        from_attributes = True


class PlaylistDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    tracks: List[PlaylistTrackItem] = []

    class Config:
        from_attributes = True


# =============================================================================
# Phase 7 — Auth schemas
# =============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    username: Optional[str] = Field(None, max_length=100)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int


class UserMeResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
