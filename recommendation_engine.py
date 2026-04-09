"""
Recommendation Engine — V2
Switches from feature-vector cosine similarity to FAISS IVF+PQ nearest-neighbour
search over CLAP 512-dim embeddings, with a BPM/key re-rank pass on top.

Falls back to the original feature-vector approach automatically when:
  - The FAISS index has not been loaded yet (cold start / index not built)
  - A track has no CLAP embedding on disk or in the DB
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone

# DB models — imported from the db/ package used by Alembic
# (backend/main.py adds the project root to sys.path so this resolves)
try:
    from db.models import Track, AudioFeature, SongEmbedding, Interaction, User
except ImportError:
    # Fallback when running directly from backend/
    from models import Track, Interaction, User          # type: ignore
    AudioFeature = None                                  # type: ignore
    SongEmbedding = None                                 # type: ignore

from schemas import RecommendationResponse, TrackResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level FAISS state — populated by load_faiss_index()
# ---------------------------------------------------------------------------
_faiss_index = None          # faiss.Index object
_track_id_map: list = []     # FAISS row -> FMA track_id
_fma_to_row: dict = {}       # FMA track_id -> FAISS row

EMBED_DIR        = Path(os.getenv("EMBED_DIR",        "data/processed/embeddings"))
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/index/faiss_ivfpq.index")
FAISS_MAP_PATH   = os.getenv("FAISS_MAP_PATH",   "data/index/track_id_map.json")
FAISS_NPROBE     = int(os.getenv("FAISS_NPROBE", "64"))


def load_faiss_index() -> bool:
    """
    Load the FAISS index and ID map into module-level state.
    Call this once at FastAPI startup (lifespan handler in main.py).
    Returns True on success, False if the index files are not present.
    """
    global _faiss_index, _track_id_map, _fma_to_row

    if not Path(FAISS_INDEX_PATH).exists():
        logger.warning(
            "FAISS index not found at %s — will use feature-vector fallback.",
            FAISS_INDEX_PATH,
        )
        return False
    if not Path(FAISS_MAP_PATH).exists():
        logger.warning("FAISS ID map not found at %s", FAISS_MAP_PATH)
        return False

    try:
        import faiss
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        _faiss_index.nprobe = FAISS_NPROBE
        with open(FAISS_MAP_PATH) as f:
            _track_id_map = json.load(f)
        _fma_to_row = {tid: i for i, tid in enumerate(_track_id_map)}
        logger.info(
            "FAISS index loaded: %d vectors (nprobe=%d)",
            _faiss_index.ntotal, FAISS_NPROBE,
        )
        return True
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc)
        return False


def faiss_ready() -> bool:
    return _faiss_index is not None and len(_track_id_map) > 0


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _load_embedding_npy(fma_track_id: int) -> Optional[np.ndarray]:
    """Load a CLAP .npy file from disk for the given FMA track ID."""
    path = EMBED_DIR / f"{fma_track_id:06d}.npy"
    if path.exists():
        return np.load(str(path)).astype("float32")
    return None


def _load_embedding_db(fma_track_id: int, db: Session) -> Optional[np.ndarray]:
    """Load a CLAP embedding from the song_embeddings DB table."""
    if SongEmbedding is None:
        return None
    row = (
        db.query(SongEmbedding)
        .join(Track, SongEmbedding.track_id == Track.id)
        .filter(
            Track.fma_track_id == fma_track_id,
            SongEmbedding.model_name == "clap",
        )
        .first()
    )
    if row is None:
        return None
    try:
        vec = row.vector if isinstance(row.vector, list) else json.loads(row.vector)
        return np.array(vec, dtype="float32")
    except Exception:
        return None


def _get_seed_vector(fma_track_id: int, db: Session) -> Optional[np.ndarray]:
    """Return a normalised (1, d) CLAP vector: .npy first, DB fallback."""
    vec = _load_embedding_npy(fma_track_id)
    if vec is None:
        vec = _load_embedding_db(fma_track_id, db)
    if vec is None:
        return None
    norm = np.linalg.norm(vec)
    if norm > 1e-9:
        vec = vec / norm
    return vec.reshape(1, -1)


def _faiss_knn(seed_vec: np.ndarray, k: int, exclude_fma_id: int) -> List[int]:
    """
    FAISS k-NN search. Returns FMA track IDs (excludes seed).
    seed_vec must be shape (1, d), already L2-normalised.
    """
    import faiss as _faiss
    _faiss.normalize_L2(seed_vec)
    _, rows = _faiss_index.search(seed_vec, k + 1)
    result = []
    for r in rows[0]:
        if r == -1:
            continue
        fma_id = _track_id_map[r]
        if fma_id == exclude_fma_id:
            continue
        result.append(fma_id)
        if len(result) >= k:
            break
    return result


# ---------------------------------------------------------------------------
# Audio feature helpers
# ---------------------------------------------------------------------------

_CHROMATIC = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_KEY_ALIASES = {"C#": "Db", "D#": "Eb", "G#": "Ab", "A#": "Bb"}
_FIFTHS_POS = {_CHROMATIC[(i * 7) % 12]: i for i in range(12)}


def _key_relation_score(k1: Optional[str], k2: Optional[str]) -> float:
    if not k1 or not k2:
        return 0.5
    k1 = _KEY_ALIASES.get(k1, k1)
    k2 = _KEY_ALIASES.get(k2, k2)
    if k1 == k2:
        return 1.0
    f1 = _FIFTHS_POS.get(k1)
    f2 = _FIFTHS_POS.get(k2)
    if f1 is None or f2 is None:
        return 0.5
    dist = min(abs(f1 - f2), 12 - abs(f1 - f2))
    return 0.6 if dist <= 2 else 0.2


def _bpm_proximity(bpm1: Optional[float], bpm2: Optional[float],
                   window: float = 15.0) -> float:
    if bpm1 is None or bpm2 is None:
        return 0.5
    return max(0.0, 1.0 - abs(bpm1 - bpm2) / window)


def _get_audio_features(track: Track, db: Session) -> Dict:
    """Prefer AudioFeature table; fall back to columns on Track itself."""
    af = None
    if AudioFeature is not None:
        af = db.query(AudioFeature).filter(AudioFeature.track_id == track.id).first()
    return {
        "tempo":            (af.tempo  if af else None) or track.tempo,
        "key":              (af.key    if af else None) or track.key,
        "energy":           (af.energy if af else None) or track.energy,
        "danceability":     af.danceability     if af else None,
        "valence":          af.valence          if af else None,
        "acousticness":     af.acousticness     if af else None,
        "instrumentalness": af.instrumentalness if af else None,
        "speechiness":      af.speechiness      if af else None,
    }


def _blend_score(embed_sim: float, seed_feat: Dict, cand_feat: Dict,
                 taste_vector: Optional[List[float]] = None) -> float:
    """
    0.70 * embed_sim + 0.20 * bpm_proximity + 0.10 * key_relation
    + optional 20% taste-vector bias.
    """
    bpm  = _bpm_proximity(seed_feat.get("tempo"), cand_feat.get("tempo"))
    key  = _key_relation_score(seed_feat.get("key"), cand_feat.get("key"))
    score = 0.70 * embed_sim + 0.20 * bpm + 0.10 * key

    if taste_vector:
        tv_sim = _feature_cosine(taste_vector, cand_feat)
        score = score * 0.80 + tv_sim * 0.20

    return round(min(score, 1.0), 4)


def _feature_cosine(taste_vector: List[float], feat: Dict) -> float:
    keys = ["tempo", "energy", "danceability", "valence",
            "acousticness", "instrumentalness", "speechiness"]
    b = np.array([feat.get(k) or 0.0 for k in keys], dtype="float32")
    a = np.array(taste_vector[: len(b)], dtype="float32")
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _why_this(seed_feat: Dict, cand_feat: Dict, embed_sim: float) -> str:
    parts = []
    if embed_sim > 0.85:
        parts.append("very similar sonic character")
    elif embed_sim > 0.65:
        parts.append("similar sound and style")
    else:
        parts.append("related sound")

    if seed_feat.get("tempo") and cand_feat.get("tempo"):
        delta = abs(seed_feat["tempo"] - cand_feat["tempo"])
        parts.append(f"close tempo ({delta:.0f} BPM apart)")

    kr = _key_relation_score(seed_feat.get("key"), cand_feat.get("key"))
    if kr == 1.0:
        parts.append("same key")
    elif kr == 0.6:
        parts.append("harmonically related key")

    return "Recommended because of " + ", ".join(parts) + "."


# ---------------------------------------------------------------------------
# Feature-vector fallback (V1 approach)
# ---------------------------------------------------------------------------

def _feature_similarity_v1(f1: Dict, f2: Dict) -> float:
    weights = {
        "tempo": 0.15, "energy": 0.20, "danceability": 0.15,
        "valence": 0.15, "acousticness": 0.10,
        "instrumentalness": 0.10, "loudness": 0.05, "speechiness": 0.10,
    }
    v1, v2 = [], []
    for feat, w in weights.items():
        a, b = f1.get(feat), f2.get(feat)
        if a is None or b is None:
            continue
        if feat == "tempo":
            a, b = (a - 60) / 120, (b - 60) / 120
        elif feat == "loudness":
            a, b = (a + 60) / 60, (b + 60) / 60
        v1.append(a * w)
        v2.append(b * w)
    if not v1:
        return 0.0
    a_arr = np.array(v1)
    b_arr = np.array(v2)
    na, nb = np.linalg.norm(a_arr), np.linalg.norm(b_arr)
    if na == 0 or nb == 0:
        return 0.0
    return float((np.dot(a_arr, b_arr) / (na * nb) + 1) / 2)


# ---------------------------------------------------------------------------
# Public RecommendationEngine class
# ---------------------------------------------------------------------------

class RecommendationEngine:
    """
    Hybrid recommendation engine — V2.

    Priority:
      1. FAISS IVF+PQ over CLAP 512-dim embeddings (when index is loaded)
      2. Feature-vector cosine similarity (fallback when FAISS unavailable)
    """

    # ------------------------------------------------------------------
    # find_similar_tracks
    # ------------------------------------------------------------------

    def find_similar_tracks(
        self,
        track_id: int,
        limit: int,
        db: Session,
        taste_vector: Optional[List[float]] = None,
    ) -> List[RecommendationResponse]:
        seed = db.query(Track).filter(Track.id == track_id).first()
        if not seed:
            return []

        seed_feat = _get_audio_features(seed, db)

        # ── FAISS path ────────────────────────────────────────────────
        if faiss_ready() and seed.fma_track_id:
            seed_vec = _get_seed_vector(seed.fma_track_id, db)
            if seed_vec is not None:
                neighbor_fma_ids = _faiss_knn(seed_vec, limit * 3, seed.fma_track_id)
                candidates = (
                    db.query(Track)
                    .filter(Track.fma_track_id.in_(neighbor_fma_ids))
                    .all()
                )
                embed_sims = self._compute_embed_sims(
                    seed_vec,
                    [c.fma_track_id for c in candidates if c.fma_track_id],
                )
                scored = []
                for c in candidates:
                    cf = _get_audio_features(c, db)
                    es = embed_sims.get(c.fma_track_id, 0.5)
                    score = _blend_score(es, seed_feat, cf, taste_vector)
                    scored.append((c, score, es, cf))

                scored.sort(key=lambda x: -x[1])
                return [
                    RecommendationResponse(
                        track_id=c.id,
                        title=c.title,
                        artist=c.artist,
                        genre=c.genre,
                        similarity_score=score,
                        reason=_why_this(seed_feat, cf, es),
                    )
                    for c, score, es, cf in scored[:limit]
                ]

        # ── Feature-vector fallback ───────────────────────────────────
        logger.info(
            "FAISS unavailable for track %d — using feature-vector fallback", track_id
        )
        return self._fallback_similar(seed, seed_feat, limit, db)

    # ------------------------------------------------------------------
    # get_personalized_recommendations
    # ------------------------------------------------------------------

    def get_personalized_recommendations(
        self,
        user_id: int,
        limit: int,
        db: Session,
    ) -> List[RecommendationResponse]:
        liked = (
            db.query(Interaction)
            .filter(
                Interaction.user_id == user_id,
                Interaction.action.in_(["like", "play", "playlist_add"]),
            )
            .order_by(desc(Interaction.created_at))
            .limit(20)
            .all()
        )
        if not liked:
            return self.get_trending_tracks(limit, db)

        interacted_ids = {
            i.track_id
            for i in db.query(Interaction).filter(Interaction.user_id == user_id).all()
        }
        liked_tracks = (
            db.query(Track)
            .filter(Track.id.in_([i.track_id for i in liked]))
            .all()
        )
        if not liked_tracks:
            return []

        # Build taste vector (mean of liked CLAP embeddings)
        taste_vecs = []
        for t in liked_tracks:
            if t.fma_track_id:
                v = _load_embedding_npy(t.fma_track_id)
                if v is not None:
                    taste_vecs.append(v)

        taste_vector: Optional[np.ndarray] = None
        if taste_vecs:
            taste_vector = np.mean(taste_vecs, axis=0).astype("float32")
            norm = np.linalg.norm(taste_vector)
            if norm > 1e-9:
                taste_vector /= norm

        genre_counts: Dict[str, int] = {}
        for t in liked_tracks:
            if t.genre:
                genre_counts[t.genre] = genre_counts.get(t.genre, 0) + 1
        fav_genre = max(genre_counts, key=genre_counts.get) if genre_counts else None

        # FAISS path: search by taste vector
        if faiss_ready() and taste_vector is not None:
            import faiss as _faiss
            qv = taste_vector.reshape(1, -1)
            _faiss.normalize_L2(qv)
            _, rows = _faiss_index.search(qv, limit * 4)
            neighbor_fma_ids = [_track_id_map[r] for r in rows[0] if r != -1]
            candidates = (
                db.query(Track)
                .filter(
                    Track.fma_track_id.in_(neighbor_fma_ids),
                    ~Track.id.in_(interacted_ids),
                )
                .all()
            )
            embed_sims = self._compute_embed_sims(
                qv, [c.fma_track_id for c in candidates if c.fma_track_id]
            )
            scored = []
            for c in candidates:
                cf = _get_audio_features(c, db)
                es = embed_sims.get(c.fma_track_id, 0.5)
                score = _blend_score(es, {}, cf)
                if fav_genre and c.genre == fav_genre:
                    score = min(1.0, score * 1.15)
                scored.append((c, score))
            scored.sort(key=lambda x: -x[1])
            return [
                RecommendationResponse(
                    track_id=c.id, title=c.title, artist=c.artist, genre=c.genre,
                    similarity_score=s, reason="Based on your listening history",
                )
                for c, s in scored[:limit]
            ]

        # Feature-vector fallback
        avg_features = {
            feat: float(
                np.mean([getattr(t, feat) for t in liked_tracks if getattr(t, feat, None)])
            )
            for feat in ["tempo", "energy"]
        }
        candidates = db.query(Track).filter(~Track.id.in_(interacted_ids)).all()
        scored_fb = []
        for c in candidates:
            cf = {"tempo": c.tempo, "energy": c.energy}
            score = _feature_similarity_v1(avg_features, cf)
            if fav_genre and c.genre == fav_genre:
                score = min(1.0, score * 1.3)
            scored_fb.append((c, score))
        scored_fb.sort(key=lambda x: -x[1])
        return [
            RecommendationResponse(
                track_id=c.id, title=c.title, artist=c.artist, genre=c.genre,
                similarity_score=s, reason="Based on your listening history",
            )
            for c, s in scored_fb[:limit]
        ]

    # ------------------------------------------------------------------
    # get_trending_tracks
    # ------------------------------------------------------------------

    def get_trending_tracks(
        self,
        limit: int,
        db: Session,
        days: int = 7,
    ) -> List[TrackResponse]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        trending = (
            db.query(Track, func.count(Interaction.id).label("cnt"))
            .join(Interaction)
            .filter(Interaction.created_at >= cutoff)
            .group_by(Track.id)
            .order_by(desc("cnt"))
            .limit(limit)
            .all()
        )
        if not trending:
            return db.query(Track).order_by(desc(Track.id)).limit(limit).all()
        return [t for t, _ in trending]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_embed_sims(
        self, seed_vec: np.ndarray, fma_ids: List[int]
    ) -> Dict[int, float]:
        """Cosine similarity between seed_vec (1, d) and each candidate .npy."""
        sims: Dict[int, float] = {}
        for fid in fma_ids:
            if fid is None:
                sims[fid] = 0.5
                continue
            cv = _load_embedding_npy(fid)
            if cv is None:
                sims[fid] = 0.5
                continue
            norm = np.linalg.norm(cv)
            if norm > 1e-9:
                cv = cv / norm
            sims[fid] = float(np.dot(seed_vec[0], cv))
        return sims

    def _fallback_similar(
        self,
        seed: Track,
        seed_feat: Dict,
        limit: int,
        db: Session,
    ) -> List[RecommendationResponse]:
        all_tracks = db.query(Track).filter(Track.id != seed.id).all()
        scored = []
        for t in all_tracks:
            tf = _get_audio_features(t, db)
            score = _feature_similarity_v1(seed_feat, tf)
            if t.genre and seed.genre and t.genre == seed.genre:
                score = min(1.0, score * 1.2)
            scored.append((t, score))
        scored.sort(key=lambda x: -x[1])
        return [
            RecommendationResponse(
                track_id=t.id, title=t.title, artist=t.artist, genre=t.genre,
                similarity_score=s,
                reason=f"Similar audio features to {seed.title}",
            )
            for t, s in scored[:limit]
        ]
