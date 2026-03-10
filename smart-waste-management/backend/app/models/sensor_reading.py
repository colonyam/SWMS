"""Sensor Reading Model"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SensorReading(Base):
    """IoT sensor reading database model"""
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(Integer, ForeignKey("waste_bins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Sensor data
    fill_level_percent = Column(Float, nullable=False)  # 0-100
    temperature_celsius = Column(Float, nullable=True)
    battery_percent = Column(Float, default=100.0)  # 0-100
    
    # Timestamp
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    bin = relationship("WasteBin", back_populates="sensor_readings")
    
    # Table indexes for performance
    __table_args__ = (
        Index('idx_reading_bin_time', 'bin_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SensorReading(bin_id={self.bin_id}, fill={self.fill_level_percent}%, time={self.timestamp})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bin_id": self.bin_id,
            "fill_level_percent": round(self.fill_level_percent, 2),
            "temperature_celsius": round(self.temperature_celsius, 2) if self.temperature_celsius else None,
            "battery_percent": round(self.battery_percent, 2),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
