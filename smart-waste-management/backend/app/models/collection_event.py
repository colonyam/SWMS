"""Collection Event Model"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CollectionEvent(Base):
    """Collection event database model - records when bins are emptied"""
    __tablename__ = "collection_events"
    
    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(Integer, ForeignKey("waste_bins.id", ondelete="CASCADE"), nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("collection_routes.id", ondelete="SET NULL"), nullable=True)
    
    # Collection details
    collected_at = Column(DateTime, server_default=func.now(), nullable=False)
    fill_level_at_collection = Column(Float, nullable=True)  # Fill level when collected
    weight_kg = Column(Float, nullable=True)  # Actual weight collected (if available)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    bin = relationship("WasteBin", back_populates="collection_events")
    route = relationship("CollectionRoute", back_populates="collection_events")
    
    def __repr__(self):
        return f"<CollectionEvent(bin_id={self.bin_id}, collected_at={self.collected_at})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bin_id": self.bin_id,
            "bin_location": self.bin.location_name if self.bin else None,
            "route_id": self.route_id,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "fill_level_at_collection": round(self.fill_level_at_collection, 2) if self.fill_level_at_collection else None,
            "weight_kg": round(self.weight_kg, 2) if self.weight_kg else None,
            "notes": self.notes,
        }
