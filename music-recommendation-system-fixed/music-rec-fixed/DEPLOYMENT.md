# Deployment Guide

This guide covers deploying the Music Recommendation System to production environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.8+
- MySQL 8.0+
- Git
- Web server (Nginx/Apache)

### Optional Software
- Docker & Docker Compose
- Redis (for caching)
- Certbot (for SSL certificates)

---

## Environment Setup

### 1. Production Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DB_USER=production_user
DB_PASSWORD=strong_random_password_here
DB_HOST=your-db-host.com
DB_PORT=3306
DB_NAME=music_production_db

# Application
APP_ENV=production
DEBUG=False

# API
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=generate-a-secure-random-key-here
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Generate Secure Keys

```python
# Generate SECRET_KEY
import secrets
print(secrets.token_urlsafe(32))
```

---

## Database Setup

### MySQL Production Setup

```sql
-- Create production database
CREATE DATABASE music_production_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create production user
CREATE USER 'production_user'@'%' IDENTIFIED BY 'strong_random_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON music_production_db.* TO 'production_user'@'%';

-- Flush privileges
FLUSH PRIVILEGES;
```

### Database Optimization

Add to MySQL configuration (`/etc/mysql/my.cnf`):

```ini
[mysqld]
# Performance
max_connections = 500
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M

# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

---

## Backend Deployment

### Option 1: Direct Deployment with Gunicorn

1. **Install production dependencies**
```bash
pip install gunicorn
```

2. **Create systemd service file**

`/etc/systemd/system/music-api.service`:
```ini
[Unit]
Description=Music Recommendation API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/music-recommendation-system/backend
Environment="PATH=/var/www/music-recommendation-system/venv/bin"
EnvironmentFile=/var/www/music-recommendation-system/backend/.env
ExecStart=/var/www/music-recommendation-system/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/music-api/access.log \
    --error-logfile /var/log/music-api/error.log

[Install]
WantedBy=multi-user.target
```

3. **Enable and start service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable music-api
sudo systemctl start music-api
sudo systemctl status music-api
```

### Option 2: Using Supervisor

1. **Install Supervisor**
```bash
sudo apt-get install supervisor
```

2. **Create Supervisor configuration**

`/etc/supervisor/conf.d/music-api.conf`:
```ini
[program:music-api]
directory=/var/www/music-recommendation-system/backend
command=/var/www/music-recommendation-system/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
autostart=true
autorestart=true
stderr_logfile=/var/log/music-api/err.log
stdout_logfile=/var/log/music-api/out.log
user=www-data
environment=PATH="/var/www/music-recommendation-system/venv/bin"
```

3. **Start with Supervisor**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start music-api
```

---

## Frontend Deployment

### Option 1: Static File Hosting

#### Nginx Configuration

`/etc/nginx/sites-available/music-frontend`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    root /var/www/music-recommendation-system/frontend;
    index index.html;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/music-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Setup with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Updated Nginx configuration with SSL:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL optimization
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    root /var/www/music-recommendation-system/frontend;
    index index.html;
    
    # ... rest of configuration
}
```

---

## Docker Deployment

### Backend Dockerfile

`backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

`docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: music-db
    restart: always
    environment:
      MYSQL_DATABASE: music_production_db
      MYSQL_USER: production_user
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql-config:/etc/mysql/conf.d
    networks:
      - music-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: music-api
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=mysql
      - DB_USER=production_user
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=music_production_db
      - APP_ENV=production
    depends_on:
      - mysql
    networks:
      - music-network
    volumes:
      - ./backend:/app

  nginx:
    image: nginx:alpine
    container_name: music-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - backend
    networks:
      - music-network

volumes:
  mysql_data:

networks:
  music-network:
    driver: bridge
```

### Deploy with Docker

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

---

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Setup

```bash
# Launch EC2 instance (Ubuntu 22.04)
# Configure security groups: 22, 80, 443, 8000

# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv nginx mysql-server git

# Clone repository
git clone https://github.com/yourusername/music-recommendation-system.git
cd music-recommendation-system
```

#### 2. RDS Database

- Create MySQL RDS instance
- Configure security groups
- Update `.env` with RDS endpoint

#### 3. Load Balancer

- Create Application Load Balancer
- Configure target groups for backend
- Set up health checks

### Heroku Deployment

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create your-music-app

# Add MySQL addon
heroku addons:create cleardb:ignite

# Get database URL
heroku config:get CLEARDB_DATABASE_URL

# Deploy
git push heroku main

# Run migrations
heroku run python seed_data.py
```

### DigitalOcean Deployment

1. Create Droplet (Ubuntu)
2. Install Docker and Docker Compose
3. Clone repository
4. Configure environment variables
5. Run with Docker Compose

---

## Monitoring

### Application Monitoring

1. **Install monitoring tools**
```bash
pip install prometheus-fastapi-instrumentator
```

2. **Add to main.py**
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Log Management

1. **Configure logging**
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10000000,
    backupCount=5
)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

2. **Centralized logging with ELK Stack**
- ElasticSearch for storage
- Logstash for processing
- Kibana for visualization

### Performance Monitoring

Use tools like:
- New Relic
- DataDog
- Sentry (error tracking)

---

## Security Checklist

- [ ] Use HTTPS only
- [ ] Set strong database passwords
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Enable SQL query logging
- [ ] Regular security updates
- [ ] Use environment variables for secrets
- [ ] Set up firewall rules
- [ ] Regular database backups

---

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

mysqldump -u production_user -p music_production_db > \
  $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup.sh
```

---

## Troubleshooting

### Common Issues

1. **Database connection fails**
   - Check credentials in `.env`
   - Verify MySQL is running
   - Check firewall rules

2. **API returns 502 Bad Gateway**
   - Check backend service status
   - Review error logs
   - Verify port configuration

3. **CORS errors**
   - Update `allow_origins` in main.py
   - Check Nginx proxy headers

4. **High CPU usage**
   - Increase worker count
   - Add caching layer (Redis)
   - Optimize database queries

### Log Locations

- Backend: `/var/log/music-api/`
- Nginx: `/var/log/nginx/`
- MySQL: `/var/log/mysql/`

---

## Rollback Procedure

```bash
# Backend rollback
sudo systemctl stop music-api
cd /var/www/music-recommendation-system/backend
git checkout previous-stable-tag
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start music-api

# Frontend rollback
cd /var/www/music-recommendation-system/frontend
git checkout previous-stable-tag
sudo systemctl reload nginx
```

---

## Performance Optimization

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_track_features ON tracks(energy, danceability, valence);
CREATE INDEX idx_interaction_created ON interactions(created_at);

-- Analyze tables
ANALYZE TABLE tracks, users, interactions;
```

### Application Optimization

1. **Add caching with Redis**
```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/tracks/{track_id}")
async def get_track(track_id: int):
    # Check cache
    cached = r.get(f"track:{track_id}")
    if cached:
        return json.loads(cached)
    
    # Get from DB and cache
    track = db.query(Track).filter(Track.id == track_id).first()
    r.setex(f"track:{track_id}", 3600, json.dumps(track))
    return track
```

2. **Use connection pooling**
Already configured in `database.py`

3. **Add CDN for static assets**
- CloudFlare
- AWS CloudFront
- Fastly

---

## Post-Deployment Checklist

- [ ] All services running
- [ ] SSL certificate valid
- [ ] Database accessible
- [ ] API health check passes
- [ ] Frontend loads correctly
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Logs rotating properly
- [ ] Documentation updated
- [ ] Team notified

---

## Support

For deployment issues:
1. Check service logs
2. Verify configuration files
3. Test database connection
4. Review Nginx configuration
5. Check firewall rules
