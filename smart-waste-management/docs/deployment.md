# Deployment Guide

## Smart Waste Management System - Deployment Options

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)

---

## Local Development

### Prerequisites
- Python 3.11+
- pip
- Virtual environment (recommended)

### Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Seed database:
```bash
curl -X POST http://localhost:8000/api/v1/seed-data
```

5. Access the application:
- Dashboard: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Dockerfile - Backend

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/waste_management.db
      - DEBUG=false
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  simulator:
    build: ./iot_simulator
    environment:
      - API_URL=http://backend:8000
      - INTERVAL=30
    depends_on:
      - backend
    restart: unless-stopped
    profiles:
      - with-simulator
```

### Build and Run

```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# Run with simulator
docker-compose --profile with-simulator up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## Production Deployment

### Environment Variables

Create `.env` file:

```env
# App Settings
DEBUG=false
APP_NAME=Smart Waste Management System

# Database
DATABASE_URL=postgresql://user:password@localhost/waste_management

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# CORS
CORS_ORIGINS=https://yourdomain.com

# Simulator
SIMULATOR_ENABLED=false

# Alerts
ALERT_FILL_THRESHOLD_HIGH=80
ALERT_FILL_THRESHOLD_CRITICAL=95
ALERT_BATTERY_THRESHOLD=20
```

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Systemd

Create `/etc/systemd/system/smart-waste.service`:

```ini
[Unit]
Description=Smart Waste Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/smart-waste-management/backend
Environment="PATH=/opt/smart-waste-management/venv/bin"
Environment="DATABASE_URL=sqlite:///./data/waste_management.db"
ExecStart=/opt/smart-waste-management/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable smart-waste
sudo systemctl start smart-waste
sudo systemctl status smart-waste
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Cloud Deployment

### Heroku

1. Create `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

2. Create `runtime.txt`:
```
python-3.11.0
```

3. Deploy:
```bash
heroku create your-app-name
git push heroku main
heroku open
```

### AWS Elastic Beanstalk

1. Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app.main:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current/backend
```

2. Deploy:
```bash
eb init -p python-3.11 your-app-name
eb create your-env-name
eb open
```

### Google Cloud Run

1. Create `cloudbuild.yaml`:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/smart-waste', './backend']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/smart-waste']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'smart-waste', '--image', 'gcr.io/$PROJECT_ID/smart-waste', '--region', 'us-central1', '--platform', 'managed']
```

2. Deploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Azure App Service

1. Create `startup.txt`:
```
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. Deploy via Azure CLI:
```bash
az webapp up --runtime PYTHON:3.11 --sku B1 --name your-app-name
```

---

## Database Migration

### SQLite to PostgreSQL

1. Export SQLite data:
```bash
sqlite3 waste_management.db .dump > dump.sql
```

2. Import to PostgreSQL:
```bash
psql -U user -d waste_management < dump.sql
```

3. Update `DATABASE_URL`:
```env
DATABASE_URL=postgresql://user:password@localhost/waste_management
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Monitoring

### Health Check Endpoint

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:00:00"
}
```

### Prometheus Metrics (Optional)

Add to `requirements.txt`:
```
prometheus-client==0.19.0
```

Expose metrics at `/metrics` endpoint.

---

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="waste_management.db"

# Create backup
cp $DB_FILE $BACKUP_DIR/waste_management_$DATE.db

# Keep only last 7 backups
ls -t $BACKUP_DIR/waste_management_*.db | tail -n +8 | xargs rm -f

echo "Backup completed: waste_management_$DATE.db"
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

---

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Database locked**
   - Check for concurrent access
   - Restart the application

3. **WebSocket connection failed**
   - Check firewall settings
   - Verify WebSocket URL

4. **CORS errors**
   - Update `CORS_ORIGINS` in config
   - Check origin headers

### Logs

```bash
# View application logs
tail -f logs/app.log

# View systemd logs
journalctl -u smart-waste -f

# View Docker logs
docker-compose logs -f backend
```

---

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable authentication
- [ ] Regular security updates
- [ ] Database backups
- [ ] Log monitoring
- [ ] Firewall configuration
