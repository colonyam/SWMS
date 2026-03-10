"""Waste Bin Model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class BinType(str, enum.Enum):
    """Types of waste bins"""
    GENERAL = "general"
    RECYCLING = "recycling"
    ORGANIC = "organic"
    HAZARDOUS = "hazardous"


class BinStatus(str, enum.Enum):
    """Bin operational status"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class WasteBin(Base):
    """Waste bin database model"""
    __tablename__ = "waste_bins"
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    bin_type = Column(Enum(BinType), default=BinType.GENERAL, nullable=False)
    capacity_liters = Column(Integer, default=240, nullable=False)
    install_date = Column(DateTime, server_default=func.now())
    status = Column(Enum(BinStatus), default=BinStatus.ACTIVE, nullable=False)
    
    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="bin", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="bin", cascade="all, delete-orphan")
    collection_events = relationship("CollectionEvent", back_populates="bin", cascade="all, delete-orphan")
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<WasteBin(id={self.id}, location='{self.location_name}', type='{self.bin_type}')>"
    
    def to_dict(self, include_latest_reading: bool = False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "bin_type": self.bin_type.value,
            "capacity_liters": self.capacity_liters,
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_latest_reading and self.sensor_readings:
            latest = max(self.sensor_readings, key=lambda r: r.timestamp)
            data["latest_reading"] = latest.to_dict()
        
        return data
