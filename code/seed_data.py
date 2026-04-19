"""
Seed script — loads real FMA track metadata from tracks.csv
Only runs if the tracks table is empty.
"""
import os
import random
from datetime import datetime, timedelta, timezone

import pandas as pd

from database import SessionLocal, engine
from models import Base, User, Track, Interaction

FMA_METADATA_DIR = os.getenv("FMA_METADATA_DIR", r"D:\music_data\raw\fma_metadata")
FMA_AUDIO_DIR    = os.getenv("FMA_AUDIO_DIR",    r"D:\music_data\raw\fma_large")
MAX_TRACKS       = int(os.getenv("SEED_MAX_TRACKS", "500"))

SAMPLE_USERS = [
    {"email": "alice@example.com",   "username": "alice_music"},
    {"email": "bob@example.com",     "username": "bob_beats"},
    {"email": "charlie@example.com", "username": "charlie_tunes"},
    {"email": "diana@example.com",   "username": "diana_sound"},
    {"email": "eve@example.com",     "username": "eve_melody"},
]

ACTIONS = ["play", "like", "skip", "playlist_add"]


def _audio_exists(fma_track_id: int) -> bool:
    """Check if the mp3 file actually exists on disk."""
    padded = f"{fma_track_id:06d}"
    folder = padded[:3]
    path   = os.path.join(FMA_AUDIO_DIR, folder, f"{padded}.mp3")
    return os.path.exists(path)


def load_fma_tracks() -> list[dict]:
    """Read tracks.csv and return rows that have audio files on disk."""
    csv_path = os.path.join(FMA_METADATA_DIR, "tracks.csv")
    if not os.path.exists(csv_path):
        print(f"WARNING: tracks.csv not found at {csv_path} — using empty list")
        return []

    # FMA tracks.csv has a multi-level header (rows 0-2)
    df = pd.read_csv(csv_path, header=[0, 1], index_col=0, low_memory=False)

    tracks = []
    for fma_id, row in df.iterrows():
        try:
            fma_id = int(fma_id)
        except (ValueError, TypeError):
            continue

        if not _audio_exists(fma_id):
            continue

        try:
            title  = str(row[("track",  "title")]).strip()  or f"Track {fma_id}"
            artist = str(row[("artist", "name")]).strip()   or "Unknown Artist"
            genre  = str(row[("track",  "genre_top")]).strip()
            if genre in ("nan", "", "None"):
                genre = None
        except Exception:
            title, artist, genre = f"Track {fma_id}", "Unknown Artist", None

        tracks.append({
            "title":        title,
            "artist":       artist,
            "genre":        genre,
            "fma_track_id": fma_id,
        })

        if len(tracks) >= MAX_TRACKS:
            break

    print(f"Found {len(tracks)} FMA tracks with audio files on disk.")
    return tracks


def seed_database():
    print("Checking if seed data needed …")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Track).first():
            print("Tracks already exist — seeding skipped.")
            return

        fma_tracks = load_fma_tracks()
        if not fma_tracks:
            print("No FMA tracks found — seeding skipped.")
            return

        print(f"Seeding {len(fma_tracks)} tracks …")
        tracks = []
        for t in fma_tracks:
            track = Track(
                title=t["title"],
                artist=t["artist"],
                genre=t["genre"],
                fma_track_id=t["fma_track_id"],
                tempo=random.uniform(60, 180),
                energy=random.uniform(0.1, 1.0),
                key=random.choice(["C","D","E","F","G","A","B"]),
            )
            db.add(track)
            tracks.append(track)
        db.commit()

        print("Seeding users …")
        users = []
        for u in SAMPLE_USERS:
            user = User(**u)
            db.add(user)
            users.append(user)
        db.commit()

        print("Seeding interactions …")
        for user in users:
            for track in random.sample(tracks, min(15, len(tracks))):
                db.add(Interaction(
                    user_id=user.id,
                    track_id=track.id,
                    action=random.choice(ACTIONS),
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                ))
        db.commit()
        print(f"Seeding complete: {len(tracks)} tracks, {len(users)} users.")

    except Exception as e:
        print(f"Seeding error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()