# 🚀 Quick Start Guide

Get the Music Recommendation System running in 5 minutes!

## Option 1: Docker (Recommended) ⚡

The fastest way to get started!

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1. **Navigate to the project directory**
```bash
cd music-recommendation-system
```

2. **Run the quick start script**
```bash
./start.sh
```

That's it! The script will:
- Start MySQL database
- Build and start the backend API
- Seed the database with sample data
- Display access URLs

3. **Access the application**
- Frontend: Open `frontend/index.html` in your browser
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Option 2: Manual Setup 🔧

### Prerequisites
- Python 3.8+
- MySQL 8.0+

### Step 1: Database Setup

```bash
# Start MySQL (if using Docker)
docker run --name music-mysql -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=music_db -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=app_password -p 3306:3306 -d mysql:8.0

# OR create database manually in MySQL
mysql -u root -p
CREATE DATABASE music_db;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON music_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional - defaults work with Docker MySQL)
cp .env.example .env
# Edit .env if needed

# Seed the database
python seed_data.py

# Start the server
python main.py
```

The API will be running at http://localhost:8000

### Step 3: Frontend Setup

```bash
# Navigate to frontend
cd ../frontend

# Option A: Use Python's built-in server
python -m http.server 3000

# Option B: Open directly in browser
# Just double-click index.html

# Option C: Use Node.js http-server
npx http-server -p 3000
```

Access at http://localhost:3000 (or just open index.html)

---

## Verify Installation ✅

1. **Check API health**
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

2. **Check database has data**
```bash
curl http://localhost:8000/stats/
```

You should see counts for users, tracks, and interactions.

3. **Open frontend**
- Open `frontend/index.html` in your browser
- You should see the Music Recommendation System interface
- Try searching for tracks or browsing the library

---

## Sample Data 📊

The system is pre-loaded with:
- **5 users** (alice@example.com, bob@example.com, etc.)
- **20 tracks** across various genres (Pop, Rock, Hip Hop, Electronic, etc.)
- **Random interactions** to demonstrate the recommendation engine

---

## Common Issues 🔧

### Port 8000 already in use
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

### Database connection error
```bash
# Check MySQL is running
docker ps | grep mysql

# Or check system MySQL
sudo systemctl status mysql
```

### Missing Python dependencies
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

---

## Next Steps 📚

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read the full documentation**: Check `README.md`
3. **Try the API**: See `TESTING.md` for examples
4. **Deploy to production**: Follow `DEPLOYMENT.md`

---

## Quick Commands Reference

```bash
# Start everything (Docker)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Restart services
docker-compose restart

# Run backend only
cd backend && python main.py

# Reseed database
cd backend && python seed_data.py
```

---

## Development Workflow

```bash
# 1. Start the database
docker-compose up mysql -d

# 2. Start backend with hot reload
cd backend
source venv/bin/activate
uvicorn main:app --reload

# 3. Open frontend in browser
# Open frontend/index.html

# Make changes and they'll reload automatically!
```

---

## Getting Help 🆘

- **API Documentation**: http://localhost:8000/docs
- **Full README**: `README.md`
- **API Guide**: `API_DOCUMENTATION.md`
- **Testing Guide**: `TESTING.md`
- **Deployment Guide**: `DEPLOYMENT.md`

---

## System Requirements

### Minimum
- 2 GB RAM
- 1 CPU core
- 500 MB disk space

### Recommended
- 4 GB RAM
- 2 CPU cores
- 2 GB disk space

---

Enjoy exploring the Music Recommendation System! 🎵
