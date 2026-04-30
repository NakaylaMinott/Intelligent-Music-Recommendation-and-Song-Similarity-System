"""
Seed script to populate database with sample data
"""
import random
from datetime import datetime, timedelta, timezone
from database import SessionLocal, engine
from models import Base, User, Track, Interaction

# Sample data
GENRES = ['Pop', 'Rock', 'Hip Hop', 'Electronic', 'Jazz', 'Classical', 'R&B', 'Country', 'Indie', 'Metal']

SAMPLE_TRACKS = [
    {"title": "Blinding Lights", "artist": "The Weeknd", "genre": "Pop"},
    {"title": "Shape of You", "artist": "Ed Sheeran", "genre": "Pop"},
    {"title": "Bohemian Rhapsody", "artist": "Queen", "genre": "Rock"},
    {"title": "Stairway to Heaven", "artist": "Led Zeppelin", "genre": "Rock"},
    {"title": "God's Plan", "artist": "Drake", "genre": "Hip Hop"},
    {"title": "HUMBLE.", "artist": "Kendrick Lamar", "genre": "Hip Hop"},
    {"title": "One More Time", "artist": "Daft Punk", "genre": "Electronic"},
    {"title": "Strobe", "artist": "deadmau5", "genre": "Electronic"},
    {"title": "Take Five", "artist": "Dave Brubeck", "genre": "Jazz"},
    {"title": "So What", "artist": "Miles Davis", "genre": "Jazz"},
    {"title": "Symphony No. 5", "artist": "Beethoven", "genre": "Classical"},
    {"title": "Four Seasons", "artist": "Vivaldi", "genre": "Classical"},
    {"title": "Redbone", "artist": "Childish Gambino", "genre": "R&B"},
    {"title": "Earned It", "artist": "The Weeknd", "genre": "R&B"},
    {"title": "Jolene", "artist": "Dolly Parton", "genre": "Country"},
    {"title": "Take Me Home, Country Roads", "artist": "John Denver", "genre": "Country"},
    {"title": "Mr. Brightside", "artist": "The Killers", "genre": "Indie"},
    {"title": "Take Me Out", "artist": "Franz Ferdinand", "genre": "Indie"},
    {"title": "Enter Sandman", "artist": "Metallica", "genre": "Metal"},
    {"title": "Master of Puppets", "artist": "Metallica", "genre": "Metal"},
]

SAMPLE_USERS = [
    {"email": "alice@example.com", "username": "alice_music"},
    {"email": "bob@example.com", "username": "bob_beats"},
    {"email": "charlie@example.com", "username": "charlie_tunes"},
    {"email": "diana@example.com", "username": "diana_sound"},
    {"email": "eve@example.com", "username": "eve_melody"},
]

ACTIONS = ['play', 'like', 'skip', 'playlist_add']


def generate_audio_features():
    """Generate random but realistic audio features"""
    return {
        'tempo': random.uniform(60, 180),
        'energy': random.uniform(0.1, 1.0),
        'danceability': random.uniform(0.1, 1.0),
        'valence': random.uniform(0.1, 1.0),
        'acousticness': random.uniform(0.0, 0.9),
        'instrumentalness': random.uniform(0.0, 0.9),
        'loudness': random.uniform(-20, -3),
        'speechiness': random.uniform(0.0, 0.5),
    }


def seed_database():
    """Populate database with sample data"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).first():
            print("Database already seeded. Skipping...")
            return
        
        print("Seeding users...")
        users = []
        for user_data in SAMPLE_USERS:
            user = User(**user_data)
            db.add(user)
            users.append(user)
        
        db.commit()
        print(f"Created {len(users)} users")
        
        print("Seeding tracks...")
        tracks = []
        for track_data in SAMPLE_TRACKS:
            features = generate_audio_features()
            track = Track(
                **track_data,
                tempo=features['tempo'],
                energy=features['energy'],
                key=random.choice(['C', 'D', 'E', 'F', 'G', 'A', 'B']),
            )
            db.add(track)
            tracks.append(track)
        
        db.commit()
        print(f"Created {len(tracks)} tracks")
        
        print("Seeding interactions...")
        interactions = []
        for user in users:
            # Each user interacts with 5-15 random tracks
            num_interactions = random.randint(5, 15)
            user_tracks = random.sample(tracks, num_interactions)
            
            for track in user_tracks:
                action = random.choice(ACTIONS)
                interaction = Interaction(
                    user_id=user.id,
                    track_id=track.id,
                    action=action,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                db.add(interaction)
                interactions.append(interaction)
        
        db.commit()
        print(f"Created {len(interactions)} interactions")
        
        print("\n" + "="*50)
        print("Database seeded successfully!")
        print("="*50)
        print(f"Total Users: {len(users)}")
        print(f"Total Tracks: {len(tracks)}")
        print(f"Total Interactions: {len(interactions)}")
        print("="*50)
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
