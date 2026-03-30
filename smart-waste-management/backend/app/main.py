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
    logger.info("Using database: %s", settings.DATABASE_URL)
    init_db()
    logger.info("Database initialized")

    # Ensure default admin exists (dev convenience)
    from app.database import SessionLocal
    from app.models.user import User, UserRole
    from app.utils.auth import get_password_hash

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.username == "collins") | (User.email == "collins@smartwaste.com")
        ).first()

        if not user:
            user = User(
                username="collins",
                email="collins@smartwaste.com",
                hashed_password=get_password_hash("colo1234"),
                full_name="Collins Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_superuser=True,
            )
            db.add(user)
            logger.info("Default admin user created (username: collins, password: colo1234)")
        else:
            # Keep user but reset credentials to the known dev default
            user.username = "collins"
            user.email = "collins@smartwaste.com"
            user.hashed_password = get_password_hash("colo1234")
            user.role = UserRole.ADMIN
            user.is_active = True
            user.is_superuser = True
            logger.info("Default admin user reset (username: collins, password: colo1234)")

        db.commit()
        logger.info("IMPORTANT: Please change the default password after first login!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error ensuring default admin: {e}")
    finally:
        db.close()
    
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
@app.get("/api")
def api_info():
    """API info endpoint"""
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


# Serve static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    def _frontend_file(filename: str) -> str:
        return os.path.join(frontend_path, filename)

    @app.get("/", response_class=HTMLResponse)
    async def serve_login():
        """Serve login page as default entry."""
        return FileResponse(_frontend_file("login.html"))

    @app.get("/login", response_class=HTMLResponse)
    async def serve_login_alias():
        return FileResponse(_frontend_file("login.html"))

    @app.get("/login.html", response_class=HTMLResponse)
    async def serve_login_html():
        return FileResponse(_frontend_file("login.html"))

    @app.get("/app", response_class=HTMLResponse)
    async def serve_app():
        """Serve main app after login."""
        return FileResponse(_frontend_file("index.html"))

    @app.get("/index.html", response_class=HTMLResponse)
    async def serve_index_html():
        return FileResponse(_frontend_file("index.html"))


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
