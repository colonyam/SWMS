"""Collection Route Model"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class RouteStatus(str, enum.Enum):
    """Route status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CollectionRoute(Base):
    """Collection route database model"""
    __tablename__ = "collection_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String(255), nullable=False)
    vehicle_id = Column(String(50), nullable=True)
    driver_name = Column(String(100), nullable=True)
    
    # Route details
    scheduled_date = Column(DateTime, nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=True)
    total_distance_km = Column(Float, nullable=True)
    
    # Status
    status = Column(Enum(RouteStatus), default=RouteStatus.PLANNED, nullable=False)
    
    # Route waypoints (ordered list of bin IDs)
    waypoints = Column(JSON, default=list)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    collection_events = relationship("CollectionEvent", back_populates="route")
    
    def __repr__(self):
        return f"<CollectionRoute(id={self.id}, name='{self.route_name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "route_name": self.route_name,
            "vehicle_id": self.vehicle_id,
            "driver_name": self.driver_name,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "total_distance_km": self.total_distance_km,
            "status": self.status.value,
            "waypoints": self.waypoints or [],
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
