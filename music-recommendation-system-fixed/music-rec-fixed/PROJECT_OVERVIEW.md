# Music Recommendation System - Project Overview

## Executive Summary

A full-stack intelligent music recommendation system that combines content-based and collaborative filtering to provide personalized song recommendations. Built with FastAPI (backend), vanilla JavaScript (frontend), and MySQL (database).

---

## Key Features

### 🎯 Core Functionality
- **Personalized Recommendations**: Based on user listening history and preferences
- **Similar Track Discovery**: Find songs similar to any track using audio features
- **Trending Tracks**: See what's popular across the platform
- **User Interactions**: Track plays, likes, skips, and playlist additions
- **Smart Search**: Search tracks by title, artist, or genre

### 🎵 Audio Features Analysis
The system analyzes tracks using multiple audio characteristics:
- **Tempo**: Beats per minute (BPM)
- **Energy**: Intensity and activity level (0-1)
- **Danceability**: Suitability for dancing (0-1)
- **Valence**: Musical positiveness (0-1)
- **Acousticness**: Acoustic vs. electronic (0-1)
- **Instrumentalness**: Vocal vs. instrumental (0-1)
- **Loudness**: Overall volume in decibels
- **Speechiness**: Presence of spoken words (0-1)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (Single Page App)                         │
│                   - HTML/CSS/JavaScript                      │
│                   - Responsive Design                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│                       (FastAPI)                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                           │  │
│  │  - Users (CRUD)                                       │  │
│  │  - Tracks (CRUD, Search)                             │  │
│  │  - Interactions (Record, Retrieve)                   │  │
│  │  - Recommendations (Personalized, Similar, Trending) │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Recommendation Engine                         │  │
│  │  - Content-Based Filtering                           │  │
│  │  - Collaborative Filtering                           │  │
│  │  - Hybrid Approach                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQLAlchemy ORM
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    MySQL Database                            │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Users     │  │   Tracks    │  │  Interactions    │   │
│  │  - id       │  │  - id       │  │  - id            │   │
│  │  - email    │  │  - title    │  │  - user_id (FK)  │   │
│  │  - username │  │  - artist   │  │  - track_id (FK) │   │
│  │  - created  │  │  - genre    │  │  - action        │   │
│  └─────────────┘  │  - features │  │  - rating        │   │
│                   │  - created  │  │  - duration      │   │
│                   └─────────────┘  │  - created       │   │
│                                    └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **ORM**: SQLAlchemy 2.0.36
- **Database Driver**: PyMySQL 1.1.1
- **Validation**: Pydantic 2.9.2
- **Server**: Uvicorn with Gunicorn workers
- **Scientific Computing**: NumPy 1.26.4

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with flexbox/grid
- **JavaScript (ES6+)**: Vanilla JS, no frameworks
- **Responsive Design**: Mobile-first approach

### Database
- **RDBMS**: MySQL 8.0
- **Character Set**: UTF-8 (utf8mb4)
- **Storage Engine**: InnoDB

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production)
- **Process Manager**: Supervisor/Systemd

---

## Recommendation Algorithms

### 1. Content-Based Filtering

Uses cosine similarity on audio feature vectors:

```python
similarity = dot(track1_features, track2_features) / 
             (norm(track1_features) * norm(track2_features))
```

**Feature Weights:**
- Energy: 20%
- Tempo: 15%
- Danceability: 15%
- Valence: 15%
- Instrumentalness: 10%
- Acousticness: 10%
- Speechiness: 10%
- Loudness: 5%

**Enhancements:**
- Genre matching bonus (1.2x multiplier)
- Feature normalization for fair comparison
- Weighted similarity scoring

### 2. Collaborative Filtering

Analyzes user behavior patterns:

**Algorithm:**
1. Extract user's listening history
2. Calculate average feature profile from liked tracks
3. Identify favorite genres
4. Find tracks matching the profile
5. Exclude already-heard tracks
6. Apply preference boosting

**Scoring Factors:**
- Audio feature similarity
- Genre preference (1.3x boost)
- Recent activity weight
- Interaction type (play, like, skip)

### 3. Hybrid Approach

Combines both methods with:
- Popularity signals
- Temporal relevance
- User engagement metrics
- Diversity optimization

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);
```

### Tracks Table
```sql
CREATE TABLE tracks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),
    genre VARCHAR(100),
    duration INT,
    -- Audio Features
    tempo FLOAT,
    key VARCHAR(10),
    energy FLOAT,
    danceability FLOAT,
    valence FLOAT,
    acousticness FLOAT,
    instrumentalness FLOAT,
    loudness FLOAT,
    speechiness FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_artist (artist),
    INDEX idx_genre (genre),
    INDEX idx_artist_genre (artist, genre)
);
```

### Interactions Table
```sql
CREATE TABLE interactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    track_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    rating INT,
    listen_duration INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    INDEX idx_user_id (user_id),
    INDEX idx_track_id (track_id),
    INDEX idx_user_track (user_id, track_id),
    INDEX idx_user_created (user_id, created_at)
);
```

---

## API Endpoints Summary

### Users
- `POST /users/` - Create user
- `GET /users/{id}` - Get user
- `GET /users/` - List users

### Tracks
- `POST /tracks/` - Create track
- `GET /tracks/{id}` - Get track
- `GET /tracks/` - List tracks (with filters)
- `GET /tracks/search/?q={query}` - Search tracks

### Interactions
- `POST /interactions/` - Record interaction
- `GET /interactions/user/{id}` - Get user interactions

### Recommendations
- `POST /recommendations/similar-tracks/?track_id={id}` - Similar tracks
- `POST /recommendations/personalized/?user_id={id}` - Personalized
- `GET /recommendations/trending/` - Trending tracks

### Utility
- `GET /health` - Health check
- `GET /stats/` - System statistics
- `GET /genres/` - Available genres

---

## Security Features

### Current Implementation
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Health check endpoints

### Recommended for Production
- JWT authentication
- API rate limiting
- HTTPS enforcement
- Database encryption
- User password hashing (bcrypt)
- Environment variable protection
- Input sanitization
- XSS prevention

---

## Performance Optimization

### Database
- Connection pooling (10 base, 20 overflow)
- Strategic indexing on common queries
- Query optimization with SQLAlchemy
- Database-level caching

### Application
- Stateless API design
- Efficient recommendation algorithms
- Lazy loading of relationships
- Response pagination

### Recommendations
- Consider Redis for caching
- CDN for static assets
- Database read replicas
- Horizontal API scaling

---

## Scalability

### Current Capacity
- Handles 100+ concurrent users
- Database: Thousands of tracks
- Response times: < 500ms for recommendations

### Scaling Strategies

**Vertical Scaling:**
- Increase server resources
- Optimize database configuration
- Add more database connections

**Horizontal Scaling:**
- Multiple API instances behind load balancer
- Database read replicas
- Separate recommendation service
- Cache layer (Redis/Memcached)

**Architecture Evolution:**
```
Current: Monolithic
    ↓
Phase 1: Monolithic + Cache
    ↓
Phase 2: Microservices
    - API Gateway
    - User Service
    - Track Service
    - Recommendation Service
    - Analytics Service
```

---

## Future Enhancements

### Short Term
- [ ] User authentication (JWT)
- [ ] Playlist management
- [ ] Track rating system
- [ ] Advanced search filters
- [ ] User profiles

### Medium Term
- [ ] Real audio streaming
- [ ] Social features (follow, share)
- [ ] Admin dashboard
- [ ] Advanced analytics
- [ ] Mobile apps (iOS/Android)

### Long Term
- [ ] Machine learning models (deep learning)
- [ ] Real-time collaborative filtering
- [ ] Integration with music APIs (Spotify, Apple Music)
- [ ] Voice control
- [ ] Smart speakers integration

---

## Development Roadmap

### Phase 1: MVP (Complete) ✅
- Basic CRUD operations
- Recommendation engine
- Simple frontend
- Docker deployment

### Phase 2: Enhancement (2-4 weeks)
- User authentication
- Improved UI/UX
- Playlist features
- Mobile responsiveness

### Phase 3: Advanced Features (1-2 months)
- Real audio streaming
- Social features
- Admin panel
- Advanced analytics

### Phase 4: Scale (3+ months)
- Microservices architecture
- Real-time features
- ML model improvements
- Mobile applications

---

## Testing Strategy

### Unit Tests
- Model validation
- Utility functions
- Algorithm correctness

### Integration Tests
- API endpoints
- Database operations
- Recommendation engine

### Performance Tests
- Load testing (Apache Bench, Locust)
- Response time benchmarks
- Database query optimization

### User Acceptance Tests
- Frontend functionality
- User workflows
- Cross-browser compatibility

---

## Deployment Options

1. **Docker Compose** (Development/Small Scale)
2. **Cloud VM** (AWS EC2, DigitalOcean)
3. **Container Orchestration** (Kubernetes, Docker Swarm)
4. **Platform as a Service** (Heroku, Google App Engine)
5. **Serverless** (AWS Lambda + API Gateway)

---

## Monitoring & Observability

### Metrics to Track
- API response times
- Error rates
- Database query performance
- Recommendation accuracy
- User engagement
- System resources (CPU, memory, disk)

### Tools
- Prometheus + Grafana (metrics)
- ELK Stack (logs)
- Sentry (error tracking)
- New Relic/DataDog (APM)

---

## Business Value

### For Users
- Discover new music matching their taste
- Save time finding songs
- Personalized experience
- Easy-to-use interface

### For Platform
- Increased user engagement
- Data-driven insights
- Scalable architecture
- Competitive feature set

### Metrics for Success
- User retention rate
- Average session duration
- Recommendation acceptance rate
- User satisfaction scores

---

## Contributing

Contributions welcome! Areas for improvement:
- Additional recommendation algorithms
- UI/UX enhancements
- Performance optimizations
- Documentation
- Test coverage
- Feature additions

---

## License & Usage

This project is provided for educational and development purposes.

For production use:
- Review security implementation
- Add proper authentication
- Configure monitoring
- Set up backups
- Review and optimize performance

---

## Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **Docker Documentation**: https://docs.docker.com/

---

**Built with ❤️ using modern web technologies**

Version: 1.0.0  
Last Updated: February 2026
