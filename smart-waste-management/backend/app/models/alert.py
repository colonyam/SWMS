"""Alert Model"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class AlertType(str, enum.Enum):
    """Types of alerts"""
    FILL_LEVEL_HIGH = "fill_level_high"
    FILL_LEVEL_CRITICAL = "fill_level_critical"
    LOW_BATTERY = "low_battery"
    SENSOR_OFFLINE = "sensor_offline"
    MAINTENANCE_REQUIRED = "maintenance_required"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    """Alert database model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(Integer, ForeignKey("waste_bins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    bin = relationship("WasteBin", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(bin_id={self.bin_id}, type='{self.alert_type}', severity='{self.severity}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bin_id": self.bin_id,
            "bin_location": self.bin.location_name if self.bin else None,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
        }
