
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from database import engine, SessionLocal
from models import Base, Track, AudioFeature


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------


def log(message: str) -> None:
    print(f"[db_update] {message}")


def get_dialect(engine: Engine) -> str:
    return engine.dialect.name.lower()


def table_exists(engine: Engine, table_name: str) -> bool:
    return inspect(engine).has_table(table_name)


def get_columns(engine: Engine, table_name: str) -> set[str]:
    if not table_exists(engine, table_name):
        return set()
    return {col["name"] for col in inspect(engine).get_columns(table_name)}


def execute_sql(engine: Engine, sql: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql))


def add_column_if_missing(
    engine: Engine,
    table_name: str,
    column_name: str,
    column_type_sql: str,
) -> None:
    """Safely add one column if it does not already exist."""
    existing = get_columns(engine, table_name)
    if column_name in existing:
        log(f"Column already exists: {table_name}.{column_name}")
        return

    if not table_exists(engine, table_name):
        log(f"Table missing, skipping column add: {table_name}.{column_name}")
        return

    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_sql}"
    execute_sql(engine, sql)
    log(f"Added column: {table_name}.{column_name}")


def create_index_if_missing(engine: Engine, table_name: str, index_name: str, columns: Iterable[str]) -> None:
    """Create a non-unique index if missing. Supports SQLite/MySQL-style syntax."""
    if not table_exists(engine, table_name):
        log(f"Table missing, skipping index: {table_name}.{index_name}")
        return

    existing_indexes = {idx["name"] for idx in inspect(engine).get_indexes(table_name)}
    if index_name in existing_indexes:
        log(f"Index already exists: {index_name}")
        return

    cols = ", ".join(columns)
    sql = f"CREATE INDEX {index_name} ON {table_name} ({cols})"
    execute_sql(engine, sql)
    log(f"Created index: {index_name}")


# -----------------------------------------------------------------------------
# Update steps
# -----------------------------------------------------------------------------


def create_missing_tables() -> None:
    """Create all missing tables defined in models.py."""
    log("Creating missing tables from SQLAlchemy models...")
    Base.metadata.create_all(bind=engine)
    log("Table check complete.")


def add_compatibility_columns() -> None:
    """
    Add columns commonly expected by schemas.py / README examples but not always
    present in older local database files.
    """
    dialect = get_dialect(engine)
    log(f"Database dialect detected: {dialect}")

    # SQLite accepts these type strings. MySQL also accepts compatible versions.
    varchar_255 = "VARCHAR(255)"
    integer = "INTEGER"
    float_type = "FLOAT"
    datetime_type = "DATETIME"

    # Track fields referenced by API schemas / frontend examples.
    add_column_if_missing(engine, "tracks", "album", varchar_255)
    add_column_if_missing(engine, "tracks", "duration", integer)
    add_column_if_missing(engine, "tracks", "loudness", float_type)
    add_column_if_missing(engine, "tracks", "created_at", datetime_type)

    # Extra interaction fields shown in README examples.
    add_column_if_missing(engine, "interactions", "rating", integer)
    add_column_if_missing(engine, "interactions", "listen_duration", integer)

    # AudioFeature can store richer audio values used by the recommender.
    add_column_if_missing(engine, "audio_features", "loudness", float_type)


def backfill_track_created_at() -> None:
    """Fill NULL tracks.created_at values if the column exists."""
    if "created_at" not in get_columns(engine, "tracks"):
        return

    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
    execute_sql(engine, f"UPDATE tracks SET created_at = '{now}' WHERE created_at IS NULL")
    log("Backfilled tracks.created_at where NULL.")


def backfill_audio_features() -> None:
    """
    Ensure every track has one audio_features row.
    This helps the recommendation engine use richer feature data when available.
    """
    db = SessionLocal()
    try:
        tracks = db.query(Track).all()
        created = 0
        for track in tracks:
            existing = db.query(AudioFeature).filter(AudioFeature.track_id == track.id).first()
            if existing:
                continue

            feature = AudioFeature(
                track_id=track.id,
                tempo=getattr(track, "tempo", None),
                key=getattr(track, "key", None),
                energy=getattr(track, "energy", None),
            )
            db.add(feature)
            created += 1

        db.commit()
        log(f"Backfilled audio_features rows created: {created}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_useful_indexes() -> None:
    """Create indexes for common lookup paths."""
    create_index_if_missing(engine, "tracks", "idx_tracks_title", ["title"])
    create_index_if_missing(engine, "tracks", "idx_tracks_artist", ["artist"])
    create_index_if_missing(engine, "tracks", "idx_tracks_genre", ["genre"])
    create_index_if_missing(engine, "tracks", "idx_tracks_fma_track_id", ["fma_track_id"])

    create_index_if_missing(engine, "interactions", "idx_interactions_user_id", ["user_id"])
    create_index_if_missing(engine, "interactions", "idx_interactions_track_id", ["track_id"])
    create_index_if_missing(engine, "interactions", "idx_interactions_user_track", ["user_id", "track_id"])
    create_index_if_missing(engine, "interactions", "idx_interactions_created_at", ["created_at"])

    create_index_if_missing(engine, "audio_features", "idx_audio_features_track_id", ["track_id"])
    create_index_if_missing(engine, "song_embeddings", "idx_song_embeddings_track_id", ["track_id"])
    create_index_if_missing(engine, "user_preferences", "idx_user_preferences_user_id", ["user_id"])


def seed_database_if_requested(force: bool = False) -> None:
    """Run the existing seed_data.py function."""
    try:
        from seed_data import seed_database
    except ImportError as exc:
        log(f"Could not import seed_database from seed_data.py: {exc}")
        return

    log("Running seed_database(...) from seed_data.py...")
    seed_database(force=force)
    log("Seeding complete.")


def print_summary() -> None:
    """Print table counts for a quick sanity check."""
    tables = [
        "users",
        "tracks",
        "genres",
        "interactions",
        "audio_features",
        "song_embeddings",
        "song_similarities",
        "user_preferences",
    ]

    log("Database summary:")
    with engine.begin() as conn:
        for table in tables:
            if not table_exists(engine, table):
                print(f"  - {table}: missing")
                continue
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            print(f"  - {table}: {count}")


# -----------------------------------------------------------------------------
# Main runner
# -----------------------------------------------------------------------------


def run(seed: bool = False, force_seed: bool = False) -> None:
    create_missing_tables()
    add_compatibility_columns()
    backfill_track_created_at()
    create_useful_indexes()

    if seed or force_seed:
        seed_database_if_requested(force=force_seed)
        # Make sure any seeded tracks also get audio feature rows.
        backfill_audio_features()
    else:
        backfill_audio_features()

    print_summary()
    log("Database update finished successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely update/repair the music recommendation database.")
    parser.add_argument("--seed", action="store_true", help="Seed sample data if the database is empty.")
    parser.add_argument("--force-seed", action="store_true", help="Clear and re-seed sample data using seed_data.py.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run(seed=args.seed, force_seed=args.force_seed)
    except SQLAlchemyError as exc:
        log(f"SQLAlchemy error: {exc}")
        sys.exit(1)
    except Exception as exc:
        log(f"Unexpected error: {exc}")
        sys.exit(1)
