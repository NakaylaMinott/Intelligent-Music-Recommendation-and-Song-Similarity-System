"""
Music Recommendation System - FastAPI Backend  (V2)
Main application entry point
"""
import sys
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

# Make the project root importable so `from db.models import ...` works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_db, engine
from models import Base, User, Track, Interaction
from schemas import (
    UserCreate, UserResponse,
    TrackCreate, TrackResponse,
    InteractionCreate, InteractionResponse,
    RecommendationRequest, RecommendationResponse,
)
from recommendation_engine import RecommendationEngine, load_faiss_index

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Lifespan handler — runs once at startup and once at shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────
    # 1. Seed the database if empty
    try:
        from seed_data import seed_database
        seed_database()
    except Exception as e:
        logger.warning("Seeding skipped or failed: %s", e)

    # 2. Load FAISS index (logs a warning and falls back gracefully if missing)
    faiss_loaded = load_faiss_index()
    if faiss_loaded:
        logger.info("V2 FAISS index ready — CLAP-based similarity active.")
    else:
        logger.warning(
            "FAISS index not loaded — running in feature-vector fallback mode. "
            "Run scripts/05_build_faiss_index.py to enable V2 similarity."
        )

    yield
    # ── SHUTDOWN (nothing to clean up for now) ───────────────────────────


# Initialize FastAPI app
app = FastAPI(
    title="Music Recommendation System API",
    description="Intelligent music recommendation and song similarity system",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()


# Serve the frontend - mount static files after API routes
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/app", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ==================== Health Check ====================
@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "online",
        "message": "Music Recommendation System API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "recommendation_engine": "initialized"
    }


# ==================== User Endpoints ====================
@app.post("/users/", response_model=UserResponse, tags=["Users"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Created user: {db_user.email}")
    return db_user


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/", response_model=List[UserResponse], tags=["Users"])
async def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


# ==================== Track Endpoints ====================
@app.post("/tracks/", response_model=TrackResponse, tags=["Tracks"])
async def create_track(track: TrackCreate, db: Session = Depends(get_db)):
    """Create a new track"""
    db_track = Track(**track.model_dump())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    logger.info(f"Created track: {db_track.title} by {db_track.artist}")
    return db_track


@app.get("/tracks/search/", response_model=List[TrackResponse], tags=["Tracks"])
async def search_tracks(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db)
):
    """Search tracks by title or artist"""
    tracks = db.query(Track).filter(
        (Track.title.contains(q)) | (Track.artist.contains(q))
    ).limit(50).all()
    return tracks


@app.get("/tracks/{track_id}", response_model=TrackResponse, tags=["Tracks"])
async def get_track(track_id: int, db: Session = Depends(get_db)):
    """Get track by ID"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@app.get("/tracks/", response_model=List[TrackResponse], tags=["Tracks"])
async def list_tracks(
    skip: int = 0,
    limit: int = 100,
    genre: Optional[str] = None,
    artist: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List tracks with optional filters"""
    query = db.query(Track)
    
    if genre:
        query = query.filter(Track.genre == genre)
    if artist:
        query = query.filter(Track.artist.contains(artist))
    
    tracks = query.offset(skip).limit(limit).all()
    return tracks


# ==================== Interaction Endpoints ====================
@app.post("/interactions/", response_model=InteractionResponse, tags=["Interactions"])
async def create_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db)
):
    """Record a user interaction with a track"""
    # Verify user exists
    user = db.query(User).filter(User.id == interaction.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify track exists
    track = db.query(Track).filter(Track.id == interaction.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    db_interaction = Interaction(**interaction.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    logger.info(f"Recorded interaction: User {interaction.user_id} {interaction.action} Track {interaction.track_id}")
    return db_interaction


@app.get("/interactions/user/{user_id}", response_model=List[InteractionResponse], tags=["Interactions"])
async def get_user_interactions(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all interactions for a specific user"""
    interactions = db.query(Interaction).filter(
        Interaction.user_id == user_id
    ).order_by(Interaction.created_at.desc()).limit(limit).all()
    return interactions


# ==================== Recommendation Endpoints ====================
@app.get("/recommendations/similar-tracks/", response_model=List[RecommendationResponse], tags=["Recommendations"])
async def get_similar_tracks(
    track_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get similar tracks based on audio features"""
    # Verify track exists
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get similar tracks
    similar_tracks = recommendation_engine.find_similar_tracks(
        track_id=track_id,
        limit=limit,
        db=db
    )
    
    return similar_tracks


@app.get("/recommendations/personalized/", response_model=List[RecommendationResponse], tags=["Recommendations"])
async def get_personalized_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get personalized recommendations based on user history"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get personalized recommendations
    recommendations = recommendation_engine.get_personalized_recommendations(
        user_id=user_id,
        limit=limit,
        db=db
    )
    
    return recommendations


@app.get("/recommendations/trending/", response_model=List[TrackResponse], tags=["Recommendations"])
async def get_trending_tracks(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get trending tracks based on recent interactions"""
    recommendations = recommendation_engine.get_trending_tracks(
        limit=limit,
        db=db
    )
    return recommendations


@app.get("/genres/", tags=["Tracks"])
async def get_genres(db: Session = Depends(get_db)):
    """Get list of all available genres"""
    genres = db.query(Track.genre).distinct().filter(Track.genre.isnot(None)).all()
    return [genre[0] for genre in genres]


@app.get("/stats/", tags=["Statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    """Get system statistics"""
    total_users = db.query(User).count()
    total_tracks = db.query(Track).count()
    total_interactions = db.query(Interaction).count()
    
    return {
        "total_users": total_users,
        "total_tracks": total_tracks,
        "total_interactions": total_interactions
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)