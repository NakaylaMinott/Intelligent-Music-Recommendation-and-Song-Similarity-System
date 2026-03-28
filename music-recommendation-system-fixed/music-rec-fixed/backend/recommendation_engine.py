"""
Recommendation Engine
Implements similarity-based and collaborative filtering recommendations
"""
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from models import Track, User, Interaction
from schemas import RecommendationResponse, TrackResponse
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Hybrid recommendation engine combining:
    1. Content-based filtering (audio features similarity)
    2. Collaborative filtering (user behavior patterns)
    3. Popularity-based recommendations
    """
    
    def __init__(self):
        self.feature_weights = {
            'tempo': 0.15,
            'energy': 0.20,
            'danceability': 0.15,
            'valence': 0.15,
            'acousticness': 0.10,
            'instrumentalness': 0.10,
            'loudness': 0.05,
            'speechiness': 0.10
        }
    
    def calculate_similarity(
        self,
        track1_features: Dict[str, float],
        track2_features: Dict[str, float]
    ) -> float:
        """
        Calculate cosine similarity between two tracks based on audio features
        
        Args:
            track1_features: Dictionary of audio features for track 1
            track2_features: Dictionary of audio features for track 2
            
        Returns:
            Similarity score between 0 and 1
        """
        features = ['tempo', 'energy', 'danceability', 'valence', 
                   'acousticness', 'instrumentalness', 'loudness', 'speechiness']
        
        # Extract and normalize features
        vec1 = []
        vec2 = []
        
        for feature in features:
            val1 = track1_features.get(feature)
            val2 = track2_features.get(feature)
            
            if val1 is None or val2 is None:
                continue
            
            # Normalize tempo (typical range 60-180 BPM)
            if feature == 'tempo':
                val1 = (val1 - 60) / 120
                val2 = (val2 - 60) / 120
            # Normalize loudness (typical range -60 to 0 dB)
            elif feature == 'loudness':
                val1 = (val1 + 60) / 60
                val2 = (val2 + 60) / 60
            
            weight = self.feature_weights.get(feature, 1.0)
            vec1.append(val1 * weight)
            vec2.append(val2 * weight)
        
        if not vec1 or not vec2:
            return 0.0
        
        # Calculate cosine similarity
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Convert to 0-1 range
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    def find_similar_tracks(
        self,
        track_id: int,
        limit: int,
        db: Session
    ) -> List[RecommendationResponse]:
        """
        Find tracks similar to the given track based on audio features
        
        Args:
            track_id: ID of the reference track
            limit: Maximum number of recommendations
            db: Database session
            
        Returns:
            List of similar tracks with similarity scores
        """
        # Get reference track
        reference_track = db.query(Track).filter(Track.id == track_id).first()
        if not reference_track:
            return []
        
        # Extract reference features
        ref_features = {
            'tempo': reference_track.tempo,
            'energy': reference_track.energy,
            'danceability': reference_track.danceability,
            'valence': reference_track.valence,
            'acousticness': reference_track.acousticness,
            'instrumentalness': reference_track.instrumentalness,
            'loudness': reference_track.loudness,
            'speechiness': reference_track.speechiness
        }
        
        # Get all other tracks
        all_tracks = db.query(Track).filter(Track.id != track_id).all()
        
        # Calculate similarities
        similarities = []
        for track in all_tracks:
            track_features = {
                'tempo': track.tempo,
                'energy': track.energy,
                'danceability': track.danceability,
                'valence': track.valence,
                'acousticness': track.acousticness,
                'instrumentalness': track.instrumentalness,
                'loudness': track.loudness,
                'speechiness': track.speechiness
            }
            
            similarity = self.calculate_similarity(ref_features, track_features)
            
            # Boost score if same genre
            if track.genre and reference_track.genre and track.genre == reference_track.genre:
                similarity = min(1.0, similarity * 1.2)
            
            similarities.append((track, similarity))
        
        # Sort by similarity and get top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similar = similarities[:limit]
        
        # Create recommendation responses
        recommendations = []
        for track, score in top_similar:
            recommendations.append(
                RecommendationResponse(
                    track_id=track.id,
                    title=track.title,
                    artist=track.artist,
                    genre=track.genre,
                    similarity_score=score,
                    reason=f"Similar audio features to {reference_track.title}"
                )
            )
        
        return recommendations
    
    def get_personalized_recommendations(
        self,
        user_id: int,
        limit: int,
        db: Session
    ) -> List[RecommendationResponse]:
        """
        Get personalized recommendations based on user's listening history
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            db: Database session
            
        Returns:
            List of personalized track recommendations
        """
        # Get user's recent liked/played tracks
        liked_interactions = db.query(Interaction).filter(
            Interaction.user_id == user_id,
            Interaction.action.in_(['like', 'play', 'playlist_add'])
        ).order_by(desc(Interaction.created_at)).limit(20).all()
        
        if not liked_interactions:
            # Fallback to trending tracks
            return self.get_trending_tracks(limit, db)
        
        # Get tracks the user already interacted with
        interacted_track_ids = {
            i.track_id for i in db.query(Interaction).filter(
                Interaction.user_id == user_id
            ).all()
        }
        
        # Calculate average features from liked tracks
        liked_track_ids = [i.track_id for i in liked_interactions]
        liked_tracks = db.query(Track).filter(Track.id.in_(liked_track_ids)).all()
        
        if not liked_tracks:
            return []
        
        # Calculate average feature profile
        avg_features = {
            'tempo': np.mean([t.tempo for t in liked_tracks if t.tempo]),
            'energy': np.mean([t.energy for t in liked_tracks if t.energy]),
            'danceability': np.mean([t.danceability for t in liked_tracks if t.danceability]),
            'valence': np.mean([t.valence for t in liked_tracks if t.valence]),
            'acousticness': np.mean([t.acousticness for t in liked_tracks if t.acousticness]),
            'instrumentalness': np.mean([t.instrumentalness for t in liked_tracks if t.instrumentalness]),
            'loudness': np.mean([t.loudness for t in liked_tracks if t.loudness]),
            'speechiness': np.mean([t.speechiness for t in liked_tracks if t.speechiness])
        }
        
        # Find favorite genre
        genre_counts = {}
        for track in liked_tracks:
            if track.genre:
                genre_counts[track.genre] = genre_counts.get(track.genre, 0) + 1
        favorite_genre = max(genre_counts.items(), key=lambda x: x[1])[0] if genre_counts else None
        
        # Get candidate tracks (not already interacted with)
        candidate_tracks = db.query(Track).filter(
            ~Track.id.in_(interacted_track_ids)
        ).all()
        
        # Calculate similarities
        similarities = []
        for track in candidate_tracks:
            track_features = {
                'tempo': track.tempo,
                'energy': track.energy,
                'danceability': track.danceability,
                'valence': track.valence,
                'acousticness': track.acousticness,
                'instrumentalness': track.instrumentalness,
                'loudness': track.loudness,
                'speechiness': track.speechiness
            }
            
            similarity = self.calculate_similarity(avg_features, track_features)
            
            # Boost score for favorite genre
            if favorite_genre and track.genre == favorite_genre:
                similarity = min(1.0, similarity * 1.3)
            
            similarities.append((track, similarity))
        
        # Sort and get top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = similarities[:limit]
        
        # Create recommendation responses
        recommendations = []
        for track, score in top_recommendations:
            recommendations.append(
                RecommendationResponse(
                    track_id=track.id,
                    title=track.title,
                    artist=track.artist,
                    genre=track.genre,
                    similarity_score=score,
                    reason="Based on your listening history"
                )
            )
        
        return recommendations
    
    def get_trending_tracks(
        self,
        limit: int,
        db: Session,
        days: int = 7
    ) -> List[TrackResponse]:
        """
        Get trending tracks based on recent interactions
        
        Args:
            limit: Maximum number of tracks
            db: Database session
            days: Number of days to consider for trending
            
        Returns:
            List of trending tracks
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Query for most interacted tracks
        trending = db.query(
            Track,
            func.count(Interaction.id).label('interaction_count')
        ).join(
            Interaction
        ).filter(
            Interaction.created_at >= cutoff_date
        ).group_by(
            Track.id
        ).order_by(
            desc('interaction_count')
        ).limit(limit).all()
        
        if not trending:
            # Fallback to random recent tracks
            return db.query(Track).order_by(desc(Track.created_at)).limit(limit).all()
        
        return [track for track, count in trending]
