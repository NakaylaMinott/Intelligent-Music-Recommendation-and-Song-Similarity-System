"""
Music Recommendation System - FastAPI Backend (V2 + Phase 7)
Main application entry point

Phase 7 additions:
  - POST /auth/register   — create account with hashed password
  - POST /auth/login      — returns JWT access token
  - POST /auth/logout     — blacklists current token
  - GET  /auth/me         — current user info
  - POST /interactions/like/{track_id} — records like AND updates persistent taste vector
"""
import sys
import os
import logging
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# Make the project root importable so `from db.models import ...` works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_db, engine
from models import Base, User, Track, Interaction, UserPreference, TokenBlacklist, AudioFeature
from schemas import (
    UserCreate, UserResponse,
    TrackCreate, TrackResponse,
    InteractionCreate, InteractionResponse,
    RecommendationRequest, RecommendationResponse,
    # Phase 7 schemas (added below in schemas.py)
    RegisterRequest, LoginResponse, UserMeResponse,
)
from recommendation_engine import RecommendationEngine, load_faiss_index, _load_embedding_npy

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# ── JWT / Auth config ─────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", secrets.token_hex(32))   # override in .env!
ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24 * 7                            # 7 days

pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2   = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Seed DB
    try:
        from seed_data import seed_database
        seed_database()
    except Exception as e:
        logger.warning("Seeding skipped or failed: %s", e)

    # 2. Load FAISS index
    faiss_loaded = load_faiss_index()
    if faiss_loaded:
        logger.info("V2 FAISS index ready — CLAP-based similarity active.")
    else:
        logger.warning(
            "FAISS index not loaded — running in feature-vector fallback mode. "
            "Run scripts/05_build_faiss_index.py to enable V2 similarity."
        )
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Music Recommendation System API",
    description="Intelligent music recommendation and song similarity system",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

recommendation_engine = RecommendationEngine()

# Serve frontend if present
# Serve frontend — checks multiple possible locations
_here = os.path.dirname(__file__)
FRONTEND_DIR = None
for _candidate in [
    os.path.join(_here, "frontend"),
    os.path.join(_here, "..", "frontend"),
    os.path.join(_here, "static"),
]:
    if os.path.exists(_candidate) and os.path.isdir(_candidate):
        FRONTEND_DIR = os.path.abspath(_candidate)
        break

if FRONTEND_DIR:
    app.mount("/static-files", StaticFiles(directory=FRONTEND_DIR), name="static-files")
    logger.info("Serving frontend from: %s", FRONTEND_DIR)

@app.get("/app", include_in_schema=False)
async def serve_frontend():
    for _candidate in [
        os.path.join(os.path.dirname(__file__), "frontend", "index.html"),
        os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"),
        os.path.join(os.path.dirname(__file__), "static", "index.html"),
    ]:
        if os.path.exists(_candidate):
            return FileResponse(_candidate)
    raise HTTPException(status_code=404, detail="Frontend not found")

# ── Auth helpers ──────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _create_token(user_id: int) -> tuple[str, str]:
    """Return (access_token, jti). jti is stored in TokenBlacklist on logout."""
    jti = secrets.token_hex(16)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), jti


def _decode_token(token: str) -> dict:
    """Decode and return payload, or raise HTTPException 401."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token.")


def get_current_user(
    token: Optional[str] = Depends(oauth2),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency: returns the logged-in User or None (for optional auth).
    Raises 401 if token is present but invalid/blacklisted.
    """
    if not token:
        return None
    payload = _decode_token(token)
    jti = payload.get("jti")
    if jti and db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked.")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found.")
    return user


def require_auth(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Dependency: same as get_current_user but raises 401 if not logged in."""
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication required.")
    return current_user


# ── Taste-vector persistence helper ──────────────────────────────────────────

def _update_taste_vector(user: User, track: Track, db: Session) -> None:
    """
    Update user_preferences.mood_preferences with a running-average taste vector
    derived from CLAP embeddings of liked tracks.
    Falls back silently if embeddings are unavailable.
    """
    import numpy as np

    # Get or create UserPreference row
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if prefs is None:
        prefs = UserPreference(user_id=user.id, mood_preferences={})
        db.add(prefs)
        db.flush()

    taste_data: dict = prefs.mood_preferences or {}
    tv   = taste_data.get("taste_vector")   # list[float] or None
    n    = taste_data.get("n_likes", 0)

    # Try to get CLAP embedding for the liked track
    fma_id = track.fma_track_id
    if fma_id is None:
        # Fall back to Essentia audio features as a lightweight taste signal
        af = db.query(AudioFeature).filter(AudioFeature.track_id == track.id).first()
        if af is None:
            return
        fv = [
            af.tempo or 0.0,
            af.energy or 0.0,
            af.danceability or 0.0,
            af.valence or 0.0,
            af.acousticness or 0.0,
            af.instrumentalness or 0.0,
            af.speechiness or 0.0,
        ]
    else:
        vec = _load_embedding_npy(fma_id)
        if vec is None:
            return
        fv = vec.tolist()

    # Running average: new_mean = (old_mean * n + new_val) / (n + 1)
    if tv is None or len(tv) != len(fv):
        tv = fv
    else:
        tv = [(tv[i] * n + fv[i]) / (n + 1) for i in range(len(fv))]

    taste_data["taste_vector"] = tv
    taste_data["n_likes"] = n + 1
    prefs.mood_preferences = taste_data
    prefs.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("Updated taste vector for user %d (n_likes=%d)", user.id, n + 1)


# =============================================================================
# Routes
# =============================================================================

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "message": "Music Recommendation System API", "version": "2.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    from recommendation_engine import faiss_ready
    return {
        "status": "healthy",
        "database": "connected",
        "recommendation_engine": "initialized",
        "faiss_index": "loaded" if faiss_ready() else "fallback_mode",
    }


# ── Auth (Phase 7) ────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=UserMeResponse, tags=["Auth"])
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new persistent user account."""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    if body.username and db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken.")

    user = User(
        email=body.email,
        username=body.username,
        password_hash=_hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered new user: %s", user.email)
    return user


@app.post("/auth/login", response_model=LoginResponse, tags=["Auth"])
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with email + password.
    Returns a Bearer JWT token valid for 7 days.
    Use the token in the Authorization header: `Bearer <token>`
    """
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not _verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token, _ = _create_token(user.id)
    logger.info("User logged in: %s", user.email)
    return LoginResponse(access_token=token, token_type="bearer", user_id=user.id)


@app.post("/auth/logout", tags=["Auth"])
async def logout(
    token: Optional[str] = Depends(oauth2),
    db: Session = Depends(get_db),
):
    """Blacklist the current JWT so it can't be reused."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = _decode_token(token)
    jti = payload.get("jti")
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    if jti:
        bl = TokenBlacklist(
            user_id=int(payload["sub"]),
            token_jti=jti,
            expires_at=exp,
        )
        db.add(bl)
        db.commit()
    return {"message": "Logged out successfully."}


@app.get("/auth/me", response_model=UserMeResponse, tags=["Auth"])
async def me(current_user: User = Depends(require_auth)):
    """Return the currently authenticated user's profile."""
    return current_user


# ── Users ─────────────────────────────────────────────────────────────────────

@app.post("/users/", response_model=UserResponse, tags=["Users"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a basic user (no password — use /auth/register for full accounts)."""
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@app.get("/users/", response_model=List[UserResponse], tags=["Users"])
async def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


# ── Tracks ────────────────────────────────────────────────────────────────────

@app.post("/tracks/", response_model=TrackResponse, tags=["Tracks"])
async def create_track(track: TrackCreate, db: Session = Depends(get_db)):
    db_track = Track(**track.model_dump())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track


@app.get("/tracks/search/", response_model=List[TrackResponse], tags=["Tracks"])
async def search_tracks(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    return db.query(Track).filter(
        (Track.title.contains(q)) | (Track.artist.contains(q))
    ).limit(50).all()


@app.get("/tracks/{track_id}", response_model=TrackResponse, tags=["Tracks"])
async def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")
    return track


@app.get("/tracks/", response_model=List[TrackResponse], tags=["Tracks"])
async def list_tracks(
    skip: int = 0,
    limit: int = 100,
    genre: Optional[str] = None,
    artist: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Track)
    if genre:
        query = query.filter(Track.genre == genre)
    if artist:
        query = query.filter(Track.artist.contains(artist))
    return query.offset(skip).limit(limit).all()


# ── Interactions ──────────────────────────────────────────────────────────────

@app.post("/interactions/", response_model=InteractionResponse, tags=["Interactions"])
async def create_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db),
):
    """Record any interaction (play, skip, like, etc.)."""
    if not db.query(User).filter(User.id == interaction.user_id).first():
        raise HTTPException(status_code=404, detail="User not found.")
    if not db.query(Track).filter(Track.id == interaction.track_id).first():
        raise HTTPException(status_code=404, detail="Track not found.")
    db_i = Interaction(**interaction.model_dump())
    db.add(db_i)
    db.commit()
    db.refresh(db_i)
    return db_i


@app.post("/interactions/like/{track_id}", tags=["Interactions"])
async def like_track(
    track_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Authenticated like endpoint.
    Records the interaction AND updates the user's persistent taste vector
    so future personalized recommendations reflect this preference.
    """
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")

    # Record interaction
    db_i = Interaction(user_id=current_user.id, track_id=track_id, action="like")
    db.add(db_i)
    db.commit()

    # Update persistent taste vector
    _update_taste_vector(current_user, track, db)

    return {"message": f"Liked '{track.title}'. Taste profile updated."}


@app.get("/interactions/user/{user_id}", response_model=List[InteractionResponse], tags=["Interactions"])
async def get_user_interactions(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return (
        db.query(Interaction)
        .filter(Interaction.user_id == user_id)
        .order_by(Interaction.created_at.desc())
        .limit(limit)
        .all()
    )


# ── Recommendations ───────────────────────────────────────────────────────────

@app.get("/recommendations/similar-tracks/", response_model=List[RecommendationResponse], tags=["Recommendations"])
async def get_similar_tracks(
    track_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Similar tracks via FAISS (V2) or feature-vector fallback.
    If the request is authenticated, the user's taste vector is used to bias results.
    """
    if not db.query(Track).filter(Track.id == track_id).first():
        raise HTTPException(status_code=404, detail="Track not found.")

    # Load taste vector for authenticated users
    taste_vector = None
    if current_user:
        prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
        if prefs and prefs.mood_preferences:
            taste_vector = prefs.mood_preferences.get("taste_vector")

    return recommendation_engine.find_similar_tracks(
        track_id=track_id, limit=limit, db=db, taste_vector=taste_vector
    )


@app.get("/recommendations/personalized/", response_model=List[RecommendationResponse], tags=["Recommendations"])
async def get_personalized_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found.")
    return recommendation_engine.get_personalized_recommendations(
        user_id=user_id, limit=limit, db=db
    )


@app.get("/recommendations/trending/", response_model=List[TrackResponse], tags=["Recommendations"])
async def get_trending_tracks(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return recommendation_engine.get_trending_tracks(limit=limit, db=db)


# ── Misc ──────────────────────────────────────────────────────────────────────

@app.get("/genres/", tags=["Tracks"])
async def get_genres(db: Session = Depends(get_db)):
    genres = db.query(Track.genre).distinct().filter(Track.genre.isnot(None)).all()
    return [g[0] for g in genres]


@app.get("/stats/", tags=["Statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "total_tracks": db.query(Track).count(),
        "total_interactions": db.query(Interaction).count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
