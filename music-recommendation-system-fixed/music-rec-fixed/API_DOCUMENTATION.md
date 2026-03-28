# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. This should be implemented for production use.

## Response Format

### Success Response
```json
{
  "id": 1,
  "title": "Track Title",
  "artist": "Artist Name",
  ...
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

## Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Endpoints

### Health Check

#### GET /
Check if the API is running.

**Response:**
```json
{
  "status": "online",
  "message": "Music Recommendation System API",
  "version": "1.0.0"
}
```

#### GET /health
Detailed health check including database and recommendation engine status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "recommendation_engine": "initialized"
}
```

---

## User Endpoints

### Create User
Create a new user account.

**Endpoint:** `POST /users/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "music_fan"  // optional
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "music_fan",
  "created_at": "2024-02-16T12:00:00Z"
}
```

**Errors:**
- `400` - Email already registered

---

### Get User
Retrieve user information by ID.

**Endpoint:** `GET /users/{user_id}`

**Path Parameters:**
- `user_id` (integer) - User ID

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "music_fan",
  "created_at": "2024-02-16T12:00:00Z"
}
```

**Errors:**
- `404` - User not found

---

### List Users
Get a paginated list of all users.

**Endpoint:** `GET /users/`

**Query Parameters:**
- `skip` (integer, default: 0) - Number of records to skip
- `limit` (integer, default: 100) - Maximum records to return

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "username": "music_fan",
    "created_at": "2024-02-16T12:00:00Z"
  }
]
```

---

## Track Endpoints

### Create Track
Add a new track to the system.

**Endpoint:** `POST /tracks/`

**Request Body:**
```json
{
  "title": "Blinding Lights",
  "artist": "The Weeknd",
  "album": "After Hours",
  "genre": "Pop",
  "duration": 200,
  "tempo": 171.0,
  "key": "C#",
  "energy": 0.73,
  "danceability": 0.51,
  "valence": 0.33,
  "acousticness": 0.0014,
  "instrumentalness": 0.0,
  "loudness": -5.934,
  "speechiness": 0.0598
}
```

**Required Fields:**
- `title` (string, 1-255 chars)
- `artist` (string, 1-255 chars)

**Optional Fields:**
- `album` (string, max 255 chars)
- `genre` (string, max 100 chars)
- `duration` (integer, >= 0) - Duration in seconds
- `tempo` (float, 0-300) - Beats per minute
- `key` (string, max 10 chars) - Musical key
- `energy` (float, 0-1) - Energy level
- `danceability` (float, 0-1) - How suitable for dancing
- `valence` (float, 0-1) - Musical positivity
- `acousticness` (float, 0-1) - Acoustic confidence
- `instrumentalness` (float, 0-1) - Instrumental prediction
- `loudness` (float) - Overall loudness in dB
- `speechiness` (float, 0-1) - Presence of spoken words

**Response (201):**
```json
{
  "id": 1,
  "title": "Blinding Lights",
  "artist": "The Weeknd",
  "album": "After Hours",
  "genre": "Pop",
  "duration": 200,
  "tempo": 171.0,
  "energy": 0.73,
  "created_at": "2024-02-16T12:00:00Z",
  ...
}
```

---

### Get Track
Retrieve track information by ID.

**Endpoint:** `GET /tracks/{track_id}`

**Path Parameters:**
- `track_id` (integer) - Track ID

**Response (200):**
```json
{
  "id": 1,
  "title": "Blinding Lights",
  "artist": "The Weeknd",
  ...
}
```

**Errors:**
- `404` - Track not found

---

### List Tracks
Get a filtered, paginated list of tracks.

**Endpoint:** `GET /tracks/`

**Query Parameters:**
- `skip` (integer, default: 0) - Number of records to skip
- `limit` (integer, default: 100) - Maximum records to return
- `genre` (string, optional) - Filter by genre
- `artist` (string, optional) - Filter by artist (partial match)

**Example:**
```
GET /tracks/?genre=Pop&limit=10
```

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    "genre": "Pop",
    ...
  }
]
```

---

### Search Tracks
Search for tracks by title or artist.

**Endpoint:** `GET /tracks/search/`

**Query Parameters:**
- `q` (string, required, min 1 char) - Search query

**Example:**
```
GET /tracks/search/?q=blinding
```

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    ...
  }
]
```

---

## Interaction Endpoints

### Record Interaction
Record a user's interaction with a track.

**Endpoint:** `POST /interactions/`

**Request Body:**
```json
{
  "user_id": 1,
  "track_id": 5,
  "action": "like",
  "rating": 5,              // optional, 1-5
  "listen_duration": 180    // optional, seconds
}
```

**Valid Actions:**
- `play` - User played the track
- `like` - User liked the track
- `skip` - User skipped the track
- `playlist_add` - User added track to playlist
- `dislike` - User disliked the track

**Response (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "track_id": 5,
  "action": "like",
  "rating": 5,
  "listen_duration": 180,
  "created_at": "2024-02-16T12:00:00Z"
}
```

**Errors:**
- `404` - User or track not found

---

### Get User Interactions
Retrieve all interactions for a specific user.

**Endpoint:** `GET /interactions/user/{user_id}`

**Path Parameters:**
- `user_id` (integer) - User ID

**Query Parameters:**
- `limit` (integer, default: 50) - Maximum records to return

**Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "track_id": 5,
    "action": "like",
    "rating": 5,
    "created_at": "2024-02-16T12:00:00Z"
  }
]
```

---

## Recommendation Endpoints

### Get Similar Tracks
Find tracks similar to a given track based on audio features.

**Endpoint:** `POST /recommendations/similar-tracks/`

**Query Parameters:**
- `track_id` (integer, required) - Reference track ID
- `limit` (integer, default: 10, min: 1, max: 50) - Number of recommendations

**Example:**
```
POST /recommendations/similar-tracks/?track_id=1&limit=10
```

**Response (200):**
```json
[
  {
    "track_id": 5,
    "title": "Save Your Tears",
    "artist": "The Weeknd",
    "genre": "Pop",
    "similarity_score": 0.89,
    "reason": "Similar audio features to Blinding Lights"
  }
]
```

**Errors:**
- `404` - Track not found

---

### Get Personalized Recommendations
Get personalized track recommendations based on user's listening history.

**Endpoint:** `POST /recommendations/personalized/`

**Query Parameters:**
- `user_id` (integer, required) - User ID
- `limit` (integer, default: 10, min: 1, max: 50) - Number of recommendations

**Example:**
```
POST /recommendations/personalized/?user_id=1&limit=20
```

**Response (200):**
```json
[
  {
    "track_id": 8,
    "title": "One More Time",
    "artist": "Daft Punk",
    "genre": "Electronic",
    "similarity_score": 0.85,
    "reason": "Based on your listening history"
  }
]
```

**Note:** If user has no interactions, returns trending tracks as fallback.

**Errors:**
- `404` - User not found

---

### Get Trending Tracks
Get currently trending tracks based on recent user interactions.

**Endpoint:** `GET /recommendations/trending/`

**Query Parameters:**
- `limit` (integer, default: 20, min: 1, max: 100) - Number of tracks

**Example:**
```
GET /recommendations/trending/?limit=20
```

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    "genre": "Pop",
    ...
  }
]
```

---

## Utility Endpoints

### Get Genres
Get list of all available genres in the system.

**Endpoint:** `GET /genres/`

**Response (200):**
```json
[
  "Pop",
  "Rock",
  "Hip Hop",
  "Electronic",
  "Jazz"
]
```

---

### Get Statistics
Get system-wide statistics.

**Endpoint:** `GET /stats/`

**Response (200):**
```json
{
  "total_users": 5,
  "total_tracks": 20,
  "total_interactions": 75
}
```

---

## Rate Limiting

Currently not implemented. For production, consider implementing rate limiting:
- 100 requests per minute per IP for general endpoints
- 10 requests per minute for recommendation endpoints

---

## CORS

The API allows cross-origin requests from all origins (`*`) by default. For production, configure specific origins in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- See request/response schemas
- Test endpoints directly from the browser
- View example requests and responses

---

## Examples

### Complete User Journey

```bash
# 1. Create a user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "username": "newbie"}'

# 2. Browse tracks
curl http://localhost:8000/tracks/?limit=10

# 3. Play a track (record interaction)
curl -X POST http://localhost:8000/interactions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "track_id": 5, "action": "play"}'

# 4. Like a track
curl -X POST http://localhost:8000/interactions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "track_id": 5, "action": "like", "rating": 5}'

# 5. Get personalized recommendations
curl -X POST "http://localhost:8000/recommendations/personalized/?user_id=1&limit=10"

# 6. Find similar tracks
curl -X POST "http://localhost:8000/recommendations/similar-tracks/?track_id=5&limit=10"
```

---

## Error Handling

### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Not Found Errors (404)
```json
{
  "detail": "User not found"
}
```

### Bad Request Errors (400)
```json
{
  "detail": "Email already registered"
}
```

---

## Best Practices

1. **Use appropriate HTTP methods**
   - GET for retrieving data
   - POST for creating resources
   - PUT for updating resources
   - DELETE for removing resources

2. **Include proper headers**
   ```
   Content-Type: application/json
   ```

3. **Handle pagination**
   - Use `skip` and `limit` parameters
   - Default limit is usually sufficient

4. **Record interactions**
   - Always record user interactions for better recommendations
   - Include optional fields like `rating` and `listen_duration` when available

5. **Error handling**
   - Check status codes
   - Parse error messages from `detail` field
   - Implement retry logic for network errors

---

## Versioning

Current version: **1.0.0**

Future versions will be available at:
- `/v1/...` (current, default)
- `/v2/...` (future)

---

## Support

For API issues or questions:
1. Check interactive documentation at `/docs`
2. Review this documentation
3. Check server logs for detailed error information
