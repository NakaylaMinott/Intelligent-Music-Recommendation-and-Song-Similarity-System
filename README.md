# Wavelength — Backend & Frontend (this folder)

This directory is a **flat Python backend** (FastAPI + SQLAlchemy) plus a **single-page frontend** served as static HTML. Files import each other as siblings (no Python package layout).

---

## Core backend

| File | What it contains |
|------|------------------|
| **`main.py`** | FastAPI application entry point: CORS, JWT auth (`/auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`), track CRUD and search, user interactions (plays/likes), **playlist** CRUD and add/remove tracks, **recommendation** routes (similar tracks, personalized, trending), **audio streaming** (`GET /audio/{track_id}`) from local FMA MP3s, optional static file mount, startup lifespan (seeding, FAISS load). |
| **`models.py`** | SQLAlchemy **ORM models**: `User`, `Track`, `Interaction`, `AudioFeature`, `SongEmbedding`, `UserPreference`, `TokenBlacklist`, `Playlist`, `PlaylistTrack`, genres, ratings, listening history, etc. Defines tables and relationships. |
| **`schemas.py`** | **Pydantic** request/response models used by FastAPI: users, tracks, interactions, recommendations, playlists, auth payloads. Validates and shapes JSON in/out of the API. |
| **`database.py`** | Thin wrapper: imports `engine` / `SessionLocal` from `db.py` and exposes **`get_db()`**, the FastAPI dependency that yields a DB session and closes it after each request. |
| **`db.py`** | **SQLAlchemy engine** and **`SessionLocal`** factory. Builds `DATABASE_URL` for **MySQL** via `pymysql` from env vars (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`). |

---

## Recommendations & data loading

| File | What it contains |
|------|------------------|
| **`recommendation_engine.py`** | **`RecommendationEngine`**: similar-track search using **FAISS** (IVF+PQ) over CLAP-style embeddings when index files exist; falls back to cosine similarity on feature vectors. Also trending and personalized recommendations using DB + optional user taste vectors. Paths configurable via env (`EMBED_DIR`, `FAISS_INDEX_PATH`, etc.). |
| **`seed_data.py`** | Optional **database seeding** (invoked from `main` lifespan): if tables are empty, can load FMA **`tracks.csv`**, create sample users, and insert tracks that have matching audio files under `FMA_AUDIO_DIR`. Controlled by env (e.g. `SEED_MAX_TRACKS`, paths). |

---

## Frontend

| File | What it contains |
|------|------------------|
| **`frontend/index.html`** | Main **Wavelength UI**: auth screen, discovery/for-you/trending/library/**playlists**/account tabs, mini player, playlist modal, toasts. Inline CSS and a large inline `<script>` that calls the FastAPI backend (same origin or `localhost:8000` in dev). This is the file to edit for UI behavior. |

---

## Deployment & dependencies

| File | What it contains |
|------|------------------|
| **`requirements.txt`** | Pip dependencies: FastAPI, uvicorn, SQLAlchemy, Alembic, PyMySQL, JWT/passlib, NumPy, **faiss-cpu**, pandas, librosa, etc. |
| **`Dockerfile`** | Builds a **Python 3.11** image, installs `requirements.txt`, copies the app, runs **`uvicorn main:app`** on port **8000**. |

---

## How it fits together

1. **`db.py`** connects to MySQL; **`models.py`** defines tables; **`main.py`** creates tables at startup (`Base.metadata.create_all`) if migrations have not already done so.
2. **`schemas.py`** defines the JSON contracts for **`main.py`** routes.
3. **`recommendation_engine.py`** is imported by **`main.py`** for `/recommendations/*` endpoints.
4. **`seed_data.py`** may run once at startup to populate an empty DB (when CSV/audio paths are available).
5. The browser loads **`frontend/index.html`**; it expects the API at the same host or at `http://localhost:8000` when opened from localhost.

For Docker orchestration (compose, DB service, volumes), see the parent **`seniorProjectDocker`** project; this `code` folder is the application source that is typically copied into the container or mounted as a volume.
