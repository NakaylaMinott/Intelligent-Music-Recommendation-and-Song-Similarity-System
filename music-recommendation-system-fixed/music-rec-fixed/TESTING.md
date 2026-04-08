# Testing Guide

This guide helps you test the Music Recommendation System API.

## Prerequisites

- Backend server running at `http://localhost:8000`
- Sample data loaded (run `python seed_data.py`)

## Testing Tools

### 1. Using cURL

#### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "recommendation_engine": "initialized"
}
```

#### Get Statistics
```bash
curl http://localhost:8000/stats/
```

### 2. Using HTTPie (more user-friendly)

Install: `pip install httpie`

```bash
# Get all tracks
http GET localhost:8000/tracks/

# Create a user
http POST localhost:8000/users/ email=test@example.com username=testuser

# Search tracks
http GET localhost:8000/tracks/search/ q==blinding
```

### 3. Using Python requests

Create `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test API health"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    assert response.status_code == 200

def test_get_tracks():
    """Test getting all tracks"""
    response = requests.get(f"{BASE_URL}/tracks/")
    tracks = response.json()
    print(f"Found {len(tracks)} tracks")
    assert response.status_code == 200
    assert len(tracks) > 0

def test_search_tracks():
    """Test track search"""
    response = requests.get(f"{BASE_URL}/tracks/search/?q=blinding")
    tracks = response.json()
    print(f"Search found {len(tracks)} tracks")
    assert response.status_code == 200

def test_create_user():
    """Test user creation"""
    data = {
        "email": f"test{random.randint(1000,9999)}@example.com",
        "username": "testuser"
    }
    response = requests.post(f"{BASE_URL}/users/", json=data)
    print("Created user:", response.json())
    assert response.status_code == 201

def test_record_interaction():
    """Test recording an interaction"""
    data = {
        "user_id": 1,
        "track_id": 1,
        "action": "play"
    }
    response = requests.post(f"{BASE_URL}/interactions/", json=data)
    print("Recorded interaction:", response.json())
    assert response.status_code == 201

def test_get_recommendations():
    """Test personalized recommendations"""
    response = requests.post(
        f"{BASE_URL}/recommendations/personalized/",
        params={"user_id": 1, "limit": 5}
    )
    recommendations = response.json()
    print(f"Got {len(recommendations)} recommendations")
    assert response.status_code == 200

def test_similar_tracks():
    """Test similar tracks"""
    response = requests.post(
        f"{BASE_URL}/recommendations/similar-tracks/",
        params={"track_id": 1, "limit": 5}
    )
    similar = response.json()
    print(f"Got {len(similar)} similar tracks")
    assert response.status_code == 200

if __name__ == "__main__":
    import random
    
    print("Running API Tests...")
    print("-" * 50)
    
    test_health()
    test_get_tracks()
    test_search_tracks()
    test_create_user()
    test_record_interaction()
    test_get_recommendations()
    test_similar_tracks()
    
    print("-" * 50)
    print("✅ All tests passed!")
```

Run with: `python test_api.py`

## Test Scenarios

### Scenario 1: New User Journey

```bash
# 1. Create a new user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newmusicfan"
  }'

# Save the user_id from response (e.g., 6)

# 2. Browse available tracks
curl http://localhost:8000/tracks/?limit=10

# 3. Play a track (track_id = 1)
curl -X POST http://localhost:8000/interactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 6,
    "track_id": 1,
    "action": "play",
    "listen_duration": 180
  }'

# 4. Like a few tracks
for track_id in 1 2 5 7 10; do
  curl -X POST http://localhost:8000/interactions/ \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": 6,
      \"track_id\": $track_id,
      \"action\": \"like\",
      \"rating\": 5
    }"
done

# 5. Get personalized recommendations
curl -X POST "http://localhost:8000/recommendations/personalized/?user_id=6&limit=10"
```

### Scenario 2: Music Discovery

```bash
# 1. Search for a specific artist
curl "http://localhost:8000/tracks/search/?q=weeknd"

# 2. Get details of a specific track
curl http://localhost:8000/tracks/1

# 3. Find similar tracks
curl -X POST "http://localhost:8000/recommendations/similar-tracks/?track_id=1&limit=10"

# 4. Browse by genre
curl "http://localhost:8000/tracks/?genre=Pop&limit=20"

# 5. Get trending tracks
curl "http://localhost:8000/recommendations/trending/?limit=20"
```

### Scenario 3: User Activity Analysis

```bash
# 1. Get a user's interaction history
curl http://localhost:8000/interactions/user/1?limit=50

# 2. Get user details
curl http://localhost:8000/users/1

# 3. Get personalized recommendations for the user
curl -X POST "http://localhost:8000/recommendations/personalized/?user_id=1&limit=20"
```

## Performance Testing

### Load Testing with Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint (1000 requests, 10 concurrent)
ab -n 1000 -c 10 http://localhost:8000/health

# Test track listing
ab -n 500 -c 10 http://localhost:8000/tracks/

# Test recommendations
ab -n 100 -c 5 -p post_data.json -T application/json \
  "http://localhost:8000/recommendations/personalized/?user_id=1&limit=10"
```

### Load Testing with Locust

Install: `pip install locust`

Create `locustfile.py`:

```python
from locust import HttpUser, task, between

class MusicAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_tracks(self):
        self.client.get("/tracks/")
    
    @task(2)
    def search_tracks(self):
        self.client.get("/tracks/search/?q=pop")
    
    @task(1)
    def get_recommendations(self):
        self.client.post("/recommendations/personalized/?user_id=1&limit=10")
    
    @task(1)
    def get_trending(self):
        self.client.get("/recommendations/trending/")
```

Run: `locust -f locustfile.py`

Visit: `http://localhost:8089`

## Automated Testing with Pytest

Create `tests/test_endpoints.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_tracks():
    response = client.get("/tracks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search_tracks():
    response = client.get("/tracks/search/?q=pop")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser"}
    )
    assert response.status_code in [201, 400]  # 400 if already exists

def test_get_trending():
    response = client.get("/recommendations/trending/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_invalid_user():
    response = client.get("/users/999999")
    assert response.status_code == 404

def test_invalid_track():
    response = client.get("/tracks/999999")
    assert response.status_code == 404
```

Run tests: `pytest tests/`

## Expected Response Times

| Endpoint | Expected Response Time |
|----------|----------------------|
| Health Check | < 10ms |
| List Tracks | < 50ms |
| Search Tracks | < 100ms |
| Get Recommendations | < 500ms |
| Similar Tracks | < 300ms |
| Record Interaction | < 50ms |

## Common Test Errors

### 1. Connection Refused
**Error:** `Failed to connect to localhost:8000`

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it
cd backend
python main.py
```

### 2. Database Error
**Error:** `Can't connect to MySQL server`

**Solution:**
```bash
# Check MySQL status
docker-compose ps

# Restart MySQL
docker-compose restart mysql
```

### 3. 404 Not Found
**Error:** Track or user not found

**Solution:**
```bash
# Seed the database
cd backend
python seed_data.py
```

### 4. Validation Error (422)
**Error:** Invalid request data

**Solution:** Check the API documentation for correct request format

## Testing Checklist

Before deploying to production:

- [ ] All health checks pass
- [ ] CRUD operations work for all entities
- [ ] Search functionality returns correct results
- [ ] Recommendations generate successfully
- [ ] Similar tracks algorithm works
- [ ] Interactions are recorded properly
- [ ] Error handling works correctly
- [ ] Response times are acceptable
- [ ] Load testing shows no bottlenecks
- [ ] Database queries are optimized

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_DATABASE: test_db
          MYSQL_ROOT_PASSWORD: test_password
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v
```

## Debugging Tips

### Enable SQL Query Logging

In `database.py`, set:
```python
engine = create_engine(
    DATABASE_URL,
    echo=True  # This enables SQL logging
)
```

### Enable Debug Mode

In `main.py`, run with:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
```

### Check Logs

```bash
# Backend logs
tail -f /var/log/music-api/access.log
tail -f /var/log/music-api/error.log

# Docker logs
docker-compose logs -f backend
```

## Success Criteria

A successful test run should:
1. Return 200/201 status codes for valid requests
2. Return appropriate error codes (400, 404) for invalid requests
3. Generate recommendations in < 500ms
4. Handle 100+ concurrent users
5. Maintain database consistency
6. Log all errors appropriately

---

For more detailed API documentation, visit: http://localhost:8000/docs
