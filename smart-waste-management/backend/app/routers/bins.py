"""Waste Bins API Router"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.waste_bin import WasteBin, BinType, BinStatus
from app.models.sensor_reading import SensorReading
from app.utils.schemas import (
    WasteBinCreate, WasteBinUpdate, WasteBinResponse,
    SensorReadingResponse, BinFilter
)

router = APIRouter(prefix="/bins", tags=["Waste Bins"])


@router.get("/", response_model=List[WasteBinResponse])
def get_bins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    bin_type: Optional[str] = None,
    status: Optional[str] = None,
    include_latest: bool = Query(True, description="Include latest sensor reading"),
    db: Session = Depends(get_db)
):
    """Get all waste bins with optional filtering"""
    query = db.query(WasteBin)
    
    if bin_type:
        query = query.filter(WasteBin.bin_type == bin_type)
    if status:
        query = query.filter(WasteBin.status == status)
    
    bins = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    result = []
    for bin_obj in bins:
        bin_dict = bin_obj.to_dict(include_latest_reading=include_latest)
        result.append(bin_dict)
    
    return result


@router.get("/{bin_id}", response_model=WasteBinResponse)
def get_bin(bin_id: int, include_history: bool = Query(False), db: Session = Depends(get_db)):
    """Get a specific waste bin by ID"""
    bin_obj = db.query(WasteBin).filter(WasteBin.id == bin_id).first()
    
    if not bin_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bin with ID {bin_id} not found"
        )
    
    result = bin_obj.to_dict(include_latest_reading=True)
    
    if include_history:
        # Include last 24 hours of readings
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(hours=24)
        readings = db.query(SensorReading).filter(
            SensorReading.bin_id == bin_id,
            SensorReading.timestamp >= since
        ).order_by(SensorReading.timestamp.desc()).all()
        
        result["recent_readings"] = [r.to_dict() for r in readings]
    
    return result


@router.post("/", response_model=WasteBinResponse, status_code=status.HTTP_201_CREATED)
def create_bin(bin_data: WasteBinCreate, db: Session = Depends(get_db)):
    """Create a new waste bin"""
    new_bin = WasteBin(
        location_name=bin_data.location_name,
        latitude=bin_data.latitude,
        longitude=bin_data.longitude,
        bin_type=bin_data.bin_type,
        capacity_liters=bin_data.capacity_liters,
        status=BinStatus.ACTIVE
    )
    
    db.add(new_bin)
    db.commit()
    db.refresh(new_bin)
    
    return new_bin.to_dict()


@router.put("/{bin_id}", response_model=WasteBinResponse)
def update_bin(bin_id: int, bin_data: WasteBinUpdate, db: Session = Depends(get_db)):
    """Update a waste bin"""
    bin_obj = db.query(WasteBin).filter(WasteBin.id == bin_id).first()
    
    if not bin_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bin with ID {bin_id} not found"
        )
    
    update_data = bin_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(bin_obj, field, value)
    
    db.commit()
    db.refresh(bin_obj)
    
    return bin_obj.to_dict(include_latest_reading=True)


@router.delete("/{bin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(bin_id: int, db: Session = Depends(get_db)):
    """Delete a waste bin"""
    bin_obj = db.query(WasteBin).filter(WasteBin.id == bin_id).first()
    
    if not bin_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bin with ID {bin_id} not found"
        )
    
    db.delete(bin_obj)
    db.commit()
    
    return None


@router.get("/{bin_id}/readings", response_model=List[SensorReadingResponse])
def get_bin_readings(
    bin_id: int,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get sensor readings for a specific bin"""
    # Verify bin exists
    bin_obj = db.query(WasteBin).filter(WasteBin.id == bin_id).first()
    if not bin_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bin with ID {bin_id} not found"
        )
    
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(hours=hours)
    
    readings = db.query(SensorReading).filter(
        SensorReading.bin_id == bin_id,
        SensorReading.timestamp >= since
    ).order_by(SensorReading.timestamp.desc()).all()
    
    return [r.to_dict() for r in readings]


@router.post("/{bin_id}/collect", response_model=dict)
def collect_bin(bin_id: int, notes: Optional[str] = None, db: Session = Depends(get_db)):
    """Record a manual collection event for a bin"""
    from app.models.collection_event import CollectionEvent
    from app.services.alert_service import AlertService
    from datetime import datetime
    
    # Verify bin exists
    bin_obj = db.query(WasteBin).filter(WasteBin.id == bin_id).first()
    if not bin_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bin with ID {bin_id} not found"
        )
    
    # Get current fill level
    latest = db.query(SensorReading).filter(
        SensorReading.bin_id == bin_id
    ).order_by(SensorReading.timestamp.desc()).first()
    
    # Create collection event
    collection = CollectionEvent(
        bin_id=bin_id,
        collected_at=datetime.now(),
        fill_level_at_collection=latest.fill_level_percent if latest else None,
        notes=notes or "Manual collection"
    )
    db.add(collection)
    db.commit()
    
    # Resolve any alerts for this bin
    alert_service = AlertService(db)
    resolved_count = alert_service.resolve_alerts_for_bin(bin_id, resolved_by="manual_collection")
    
    return {
        "message": "Collection recorded successfully",
        "collection_id": collection.id,
        "alerts_resolved": resolved_count
    }


@router.get("/stats/summary", response_model=dict)
def get_bins_summary(db: Session = Depends(get_db)):
    """Get summary statistics for all bins"""
    from sqlalchemy import func
    
    total = db.query(WasteBin).count()
    
    by_type = db.query(WasteBin.bin_type, func.count(WasteBin.id)).group_by(WasteBin.bin_type).all()
    by_status = db.query(WasteBin.status, func.count(WasteBin.id)).group_by(WasteBin.status).all()
    
    return {
        "total_bins": total,
        "by_type": {t.value: c for t, c in by_type},
        "by_status": {s.value: c for s, c in by_status}
    }
