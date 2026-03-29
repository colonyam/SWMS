"""Database models package"""
from app.models.waste_bin import WasteBin
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert
from app.models.collection_route import CollectionRoute
from app.models.collection_event import CollectionEvent
from app.models.user import User, UserRole

__all__ = [
    "WasteBin",
    "SensorReading", 
    "Alert",
    "CollectionRoute",
    "CollectionEvent",
    "User",
    "UserRole"
]
