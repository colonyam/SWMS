"""FastAPI Application Entry Point"""
from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
import logging
import os

from app.config import get_settings
from app.database import init_db, engine
from app.websocket import handle_websocket, manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up Smart Waste Management System...")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="IoT-based Smart Waste Management System with Real-time Monitoring and Analytics",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.routers import bins, readings, analytics, alerts, routes, auth

app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/{settings.API_VERSION}")
app.include_router(bins.router, prefix=f"{settings.API_PREFIX}/{settings.API_VERSION}")
app.include_router(readings.router, prefix=f"{settings.API_PREFIX}/{settings.API_VERSION}")
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/{settings.API_VERSION}")
app.include_router(alerts.router, prefix=f"{settings.API_PREFIX}/{settings.API_VERSION}")
app.include_router(routes.router, prefix=f"{settings.API_PREFIX}/{settings.API_VERSION}")


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await handle_websocket(websocket)


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


# API info endpoint
@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "api_prefix": f"{settings.API_PREFIX}/{settings.API_VERSION}",
        "endpoints": {
            "auth": f"{settings.API_PREFIX}/{settings.API_VERSION}/auth",
            "bins": f"{settings.API_PREFIX}/{settings.API_VERSION}/bins",
            "readings": f"{settings.API_PREFIX}/{settings.API_VERSION}/readings",
            "analytics": f"{settings.API_PREFIX}/{settings.API_VERSION}/analytics",
            "alerts": f"{settings.API_PREFIX}/{settings.API_VERSION}/alerts",
            "routes": f"{settings.API_PREFIX}/{settings.API_VERSION}/routes",
            "websocket": "/ws"
        }
    }


# Create default admin user on startup
@app.on_event("startup")
async def create_default_admin():
    """Create default admin user if no users exist"""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.user import User, UserRole
    from app.utils.auth import get_password_hash
    
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()
        if user_count == 0:
            # Create default admin user
            admin = User(
                username="admin",
                email="admin@smartwaste.com",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created (username: admin, password: admin123)")
            logger.info("IMPORTANT: Please change the default password after first login!")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
    finally:
        db.close()


# Serve static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path)), name="static")
    
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_frontend(full_path: str):
        """Serve frontend HTML"""
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return f.read()
        return HTMLResponse(content="<h1>Smart Waste Management System</h1><p>Frontend not built yet.</p>")


# Seed data endpoint for development
@app.post("/api/v1/seed-data")
def seed_data():
    """Seed database with sample data for development"""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.waste_bin import WasteBin, BinType, BinStatus
    from app.models.sensor_reading import SensorReading
    from datetime import datetime, timedelta
    import random
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(WasteBin).first()
        if existing:
            return {"message": "Database already has data. Skipping seed."}
        
        # Sample bin locations
        sample_bins = [
            {"name": "Downtown Main St", "lat": 40.7128, "lon": -74.0060, "type": BinType.GENERAL},
            {"name": "Central Park West", "lat": 40.7829, "lon": -73.9654, "type": BinType.RECYCLING},
            {"name": "Times Square", "lat": 40.7580, "lon": -73.9855, "type": BinType.GENERAL},
            {"name": "Brooklyn Bridge", "lat": 40.7061, "lon": -73.9969, "type": BinType.GENERAL},
            {"name": "Wall Street", "lat": 40.7074, "lon": -74.0113, "type": BinType.RECYCLING},
            {"name": "Madison Square", "lat": 40.7411, "lon": -73.9897, "type": BinType.ORGANIC},
            {"name": "Empire State", "lat": 40.7484, "lon": -73.9857, "type": BinType.GENERAL},
            {"name": "Grand Central", "lat": 40.7527, "lon": -73.9772, "type": BinType.GENERAL},
            {"name": "Union Square", "lat": 40.7359, "lon": -73.9908, "type": BinType.RECYCLING},
            {"name": "Chelsea Market", "lat": 40.7424, "lon": -74.0061, "type": BinType.ORGANIC},
            {"name": "High Line Park", "lat": 40.7480, "lon": -74.0048, "type": BinType.RECYCLING},
            {"name": "Battery Park", "lat": 40.7033, "lon": -74.0170, "type": BinType.GENERAL},
            {"name": "Chinatown", "lat": 40.7158, "lon": -73.9970, "type": BinType.GENERAL},
            {"name": "Little Italy", "lat": 40.7191, "lon": -73.9973, "type": BinType.ORGANIC},
            {"name": "Soho", "lat": 40.7233, "lon": -74.0030, "type": BinType.RECYCLING},
        ]
        
        created_bins = []
        for bin_data in sample_bins:
            bin_obj = WasteBin(
                location_name=bin_data["name"],
                latitude=bin_data["lat"],
                longitude=bin_data["lon"],
                bin_type=bin_data["type"],
                capacity_liters=random.choice([120, 240, 360]),
                status=BinStatus.ACTIVE
            )
            db.add(bin_obj)
            db.flush()
            created_bins.append(bin_obj)
            
            # Generate some historical readings
            base_fill = random.uniform(20, 60)
            for i in range(48):  # Last 24 hours, every 30 minutes
                reading = SensorReading(
                    bin_id=bin_obj.id,
                    fill_level_percent=min(100, base_fill + (i * random.uniform(0.5, 2))),
                    temperature_celsius=random.uniform(15, 30),
                    battery_percent=random.uniform(70, 100),
                    timestamp=datetime.now() - timedelta(minutes=i * 30)
                )
                db.add(reading)
        
        db.commit()
        
        return {
            "message": "Database seeded successfully",
            "bins_created": len(created_bins),
            "readings_created": len(created_bins) * 48
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding data: {e}")
        raise HTTPException(status_code=500, detail=f"Error seeding data: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
