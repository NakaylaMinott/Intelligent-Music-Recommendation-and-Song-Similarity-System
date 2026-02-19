"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ==================== User Schemas ====================
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user"""
    username: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    username: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Track Schemas ====================
class TrackBase(BaseModel):
    """Base track schema"""
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    album: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = Field(None, ge=0)


class TrackCreate(TrackBase):
    """Schema for creating a track"""
    tempo: Optional[float] = Field(None, ge=0, le=300)
    key: Optional[str] = Field(None, max_length=10)
    energy: Optional[float] = Field(None, ge=0, le=1)
    danceability: Optional[float] = Field(None, ge=0, le=1)
    valence: Optional[float] = Field(None, ge=0, le=1)
    acousticness: Optional[float] = Field(None, ge=0, le=1)
    instrumentalness: Optional[float] = Field(None, ge=0, le=1)
    loudness: Optional[float] = None
    speechiness: Optional[float] = Field(None, ge=0, le=1)


class TrackResponse(TrackBase):
    """Schema for track response"""
    id: int
    tempo: Optional[float]
    key: Optional[str]
    energy: Optional[float]
    danceability: Optional[float]
    valence: Optional[float]
    acousticness: Optional[float]
    instrumentalness: Optional[float]
    loudness: Optional[float]
    speechiness: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Interaction Schemas ====================
class InteractionBase(BaseModel):
    """Base interaction schema"""
    user_id: int
    track_id: int
    action: str = Field(..., pattern="^(play|like|skip|playlist_add|dislike)$")


class InteractionCreate(InteractionBase):
    """Schema for creating an interaction"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    listen_duration: Optional[int] = Field(None, ge=0)


class InteractionResponse(InteractionBase):
    """Schema for interaction response"""
    id: int
    rating: Optional[int]
    listen_duration: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Recommendation Schemas ====================
class RecommendationRequest(BaseModel):
    """Schema for recommendation request"""
    user_id: Optional[int] = None
    track_id: Optional[int] = None
    limit: int = Field(10, ge=1, le=50)
    genre: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    track_id: int
    title: str
    artist: str
    genre: Optional[str]
    similarity_score: float = Field(..., ge=0, le=1)
    reason: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Statistics Schemas ====================
class TrackStatistics(BaseModel):
    """Schema for track statistics"""
    track_id: int
    play_count: int
    like_count: int
    skip_count: int
    average_rating: Optional[float]


class UserStatistics(BaseModel):
    """Schema for user statistics"""
    user_id: int
    total_interactions: int
    favorite_genre: Optional[str]
    total_listening_time: Optional[int]  # seconds


# ==================== Bulk Operations ====================
class BulkTrackCreate(BaseModel):
    """Schema for creating multiple tracks at once"""
    tracks: List[TrackCreate]

    @field_validator('tracks')
    @classmethod
    def validate_tracks_count(cls, v):
        if len(v) > 100:
            raise ValueError('Cannot create more than 100 tracks at once')
        return v
