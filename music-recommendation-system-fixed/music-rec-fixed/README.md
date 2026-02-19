# 🎵 Intelligent Music Recommendation System

A full-stack music recommendation system that uses audio features and user behavior to provide personalized song recommendations.

## 🌟 Features

### Backend Features
- **RESTful API** built with FastAPI
- **Content-Based Filtering**: Recommendations based on audio features (tempo, energy, danceability, etc.)
- **Collaborative Filtering**: User behavior-based recommendations
- **Hybrid Recommendation Engine**: Combines multiple algorithms for better accuracy
- **User Interaction Tracking**: Play, like, skip, and playlist actions
- **Trending Tracks**: Popular tracks based on recent interactions
- **Similar Track Discovery**: Find songs similar to a given track
- **MySQL Database**: Scalable data storage with SQLAlchemy ORM

### Frontend Features
- **Modern, Responsive UI**: Works on desktop and mobile devices
- **Track Discovery**: Search and browse music library
- **Personalized Recommendations**: Get custom song suggestions based on listening history
- **Trending Section**: See what's popular right now
- **Interactive Actions**: Play, like, and explore similar tracks
- **Real-time Statistics**: View system metrics

## 🏗️ Architecture

```
music-recommendation-system/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── models.py                  # SQLAlchemy models
│   ├── schemas.py                 # Pydantic schemas
│   ├── database.py                # Database configuration
│   ├── recommendation_engine.py   # Recommendation algorithms
│   ├── seed_data.py              # Sample data generator
│   ├── requirements.txt          # Python dependencies
│   └── .env.example              # Environment variables template
└── frontend/
    └── index.html                # Single-page application
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- Modern web browser

### Backend Setup

1. **Navigate to backend directory**
```bash
cd music-recommendation-system/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up MySQL database**

Option A: Using Docker
```bash
docker-compose up -d
```

Option B: Manual MySQL setup
```sql
CREATE DATABASE music_db;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON music_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

5. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

6. **Run database migrations**
```bash
# The tables will be created automatically on first run
python main.py
```

7. **Seed the database with sample data**
```bash
python seed_data.py
```

8. **Start the backend server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd music-recommendation-system/frontend
```

2. **Serve the application**

Option A: Using Python's built-in server
```bash
python -m http.server 3000
```

Option B: Using Node.js http-server
```bash
npx http-server -p 3000
```

Option C: Open directly in browser
```bash
# Simply open index.html in your browser
```

3. **Access the application**

Open your browser and navigate to `http://localhost:3000`

## 📚 API Documentation

### Users

#### Create User
```http
POST /users/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "music_lover"
}
```

#### Get User
```http
GET /users/{user_id}
```

#### List Users
```http
GET /users/?skip=0&limit=100
```

### Tracks

#### Create Track
```http
POST /tracks/
Content-Type: application/json

{
  "title": "Song Name",
  "artist": "Artist Name",
  "genre": "Pop",
  "album": "Album Name",
  "duration": 240,
  "tempo": 120.5,
  "energy": 0.8,
  "danceability": 0.75,
  "valence": 0.6,
  "acousticness": 0.3,
  "instrumentalness": 0.0,
  "loudness": -5.2,
  "speechiness": 0.05
}
```

#### Get Track
```http
GET /tracks/{track_id}
```

#### List Tracks
```http
GET /tracks/?skip=0&limit=100&genre=Pop&artist=Drake
```

#### Search Tracks
```http
GET /tracks/search/?q=bohemian
```

### Interactions

#### Record Interaction
```http
POST /interactions/
Content-Type: application/json

{
  "user_id": 1,
  "track_id": 5,
  "action": "like",
  "rating": 5,
  "listen_duration": 180
}
```

Valid actions: `play`, `like`, `skip`, `playlist_add`, `dislike`

#### Get User Interactions
```http
GET /interactions/user/{user_id}?limit=50
```

### Recommendations

#### Get Similar Tracks
```http
POST /recommendations/similar-tracks/?track_id=1&limit=10
```

Returns tracks similar to the specified track based on audio features.

#### Get Personalized Recommendations
```http
POST /recommendations/personalized/?user_id=1&limit=20
```

Returns personalized recommendations based on user's listening history.

#### Get Trending Tracks
```http
GET /recommendations/trending/?limit=20
```

Returns currently trending tracks based on recent interactions.

### Statistics

#### Get System Stats
```http
GET /stats/
```

Returns:
```json
{
  "total_users": 5,
  "total_tracks": 20,
  "total_interactions": 75
}
```

#### Get Available Genres
```http
GET /genres/
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database Configuration
DB_USER=app_user
DB_PASSWORD=app_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=music_db

# Application Configuration
APP_ENV=development
DEBUG=True

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Database Schema

#### Users Table
- `id`: Primary key
- `email`: Unique email address
- `username`: Optional username
- `created_at`: Account creation timestamp

#### Tracks Table
- `id`: Primary key
- `title`: Song title
- `artist`: Artist name
- `album`: Album name
- `genre`: Music genre
- `duration`: Song length in seconds
- Audio features: `tempo`, `key`, `energy`, `danceability`, `valence`, `acousticness`, `instrumentalness`, `loudness`, `speechiness`
- `created_at`: Record creation timestamp

#### Interactions Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `track_id`: Foreign key to tracks
- `action`: Type of interaction (play, like, skip, etc.)
- `rating`: Optional 1-5 star rating
- `listen_duration`: How long the user listened (seconds)
- `created_at`: Interaction timestamp

## 🧮 Recommendation Algorithms

### Content-Based Filtering

Uses cosine similarity on audio features:

```python
Features:
- Tempo (BPM)           - Weight: 0.15
- Energy                - Weight: 0.20
- Danceability          - Weight: 0.15
- Valence (positivity)  - Weight: 0.15
- Acousticness          - Weight: 0.10
- Instrumentalness      - Weight: 0.10
- Loudness (dB)         - Weight: 0.05
- Speechiness           - Weight: 0.10
```

The algorithm:
1. Extracts feature vectors from tracks
2. Normalizes features to 0-1 range
3. Applies feature weights
4. Calculates cosine similarity
5. Boosts tracks in the same genre (1.2x multiplier)

### Collaborative Filtering

Based on user behavior patterns:
1. Analyzes user's liked/played tracks
2. Calculates average feature profile
3. Identifies favorite genres
4. Finds tracks matching the profile
5. Excludes already-heard tracks
6. Applies genre preference boosting (1.3x multiplier)

### Hybrid Approach

Combines both methods with popularity signals for optimal recommendations.

## 🎨 Frontend Usage

### Discover Tab
- Search for tracks by title or artist
- View all available tracks
- Play and like songs
- Find similar tracks

### For You Tab
- Select your user profile
- View personalized recommendations
- See match percentages
- Discover new music based on your taste

### Trending Tab
- Browse popular tracks
- See what other users are listening to
- Discover trending music

### Library Tab
- Browse complete music catalog
- Explore all available tracks

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Get all tracks
curl http://localhost:8000/tracks/

# Search for tracks
curl "http://localhost:8000/tracks/search/?q=blinding"

# Get recommendations for user
curl -X POST "http://localhost:8000/recommendations/personalized/?user_id=1&limit=10"
```

### Sample Data

The `seed_data.py` script creates:
- 5 sample users
- 20 tracks across various genres
- Random interactions for each user

## 📈 Performance Optimization

### Database Indexes
- User email (unique index)
- Track title, artist, genre
- Interaction composite indexes on (user_id, track_id) and (user_id, created_at)

### Caching Strategies
- Consider implementing Redis for:
  - Frequently accessed tracks
  - Trending calculations
  - User recommendation cache

### Scaling Considerations
- Database connection pooling configured (10 connections, 20 overflow)
- Stateless API design enables horizontal scaling
- Consider separating recommendation engine to microservice

## 🔐 Security

### Current Implementation
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- CORS configured (update for production)

### Production Recommendations
- Add authentication (JWT tokens)
- Implement rate limiting
- Use HTTPS only
- Set specific CORS origins
- Add API key authentication
- Implement user password hashing

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test connection
mysql -u app_user -p -h localhost
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Frontend Can't Connect to Backend
1. Check backend is running: `http://localhost:8000/health`
2. Verify CORS settings in `main.py`
3. Check browser console for errors
4. Ensure frontend is using correct API URL

## 🚀 Deployment

### Backend Deployment (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
- Use environment variables for configuration
- Set `APP_ENV=production`
- Configure proper database credentials
- Set up reverse proxy (nginx)

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional recommendation algorithms
- User authentication
- Playlist management
- Social features
- Audio streaming integration
- Machine learning model improvements

## 📞 Support

For issues and questions:
- Check API documentation at `/docs`
- Review troubleshooting section
- Check database connection
- Verify all dependencies are installed

## 🎯 Future Enhancements

- [ ] Real audio file streaming
- [ ] User authentication and authorization
- [ ] Playlist creation and management
- [ ] Social features (follow users, share playlists)
- [ ] Advanced ML models (deep learning embeddings)
- [ ] A/B testing framework for recommendations
- [ ] Real-time collaborative filtering
- [ ] Integration with music APIs (Spotify, Apple Music)
- [ ] Mobile applications (iOS/Android)
- [ ] Admin dashboard

---

Built with ❤️ using FastAPI and modern web technologies
