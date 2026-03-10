"""Sensor Readings API Router"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.sensor_reading import SensorReading
from app.models.waste_bin import WasteBin
from app.services.alert_service import AlertService
from app.utils.schemas import SensorReadingCreate, SensorReadingResponse

router = APIRouter(prefix="/readings", tags=["Sensor Readings"])


@router.get("/", response_model=List[SensorReadingResponse])
def get_readings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    bin_id: Optional[int] = None,
    hours: Optional[int] = Query(None, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get sensor readings with optional filtering"""
    query = db.query(SensorReading)
    
    if bin_id:
        query = query.filter(SensorReading.bin_id == bin_id)
    
    if hours:
        since = datetime.now() - timedelta(hours=hours)
        query = query.filter(SensorReading.timestamp >= since)
    
    readings = query.order_by(SensorReading.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [r.to_dict() for r in readings]


@router.get("/latest", response_model=List[dict])
def get_latest_readings(db: Session = Depends(get_db)):
    """Get the latest reading for each bin"""
    from sqlalchemy import func, and_
    
    # Subquery to get latest timestamp per bin
    subquery = db.query(
        SensorReading.bin_id,
        func.max(SensorReading.timestamp).label('max_time')
    ).group_by(SensorReading.bin_id).subquery()
    
    # Join to get full reading data
    readings = db.query(SensorReading, WasteBin.location_name).join(
        subquery,
        and_(
            SensorReading.bin_id == subquery.c.bin_id,
            SensorReading.timestamp == subquery.c.max_time
        )
    ).join(WasteBin, SensorReading.bin_id == WasteBin.id).all()
    
    result = []
    for reading, location in readings:
        data = reading.to_dict()
        data['bin_location'] = location
        result.append(data)
    
    return result


@router.post("/", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
def create_reading(reading_data: SensorReadingCreate, db: Session = Depends(get_db)):
    """Submit a new sensor reading (from IoT device)"""
    # Verify bin exists
    bin_obj = db.query(WasteBin).filter(WasteBin.id == reading_data.bin_id).first()
    if not bin_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bin with ID {reading_data.bin_id} not found"
        )
    
    # Create reading
    new_reading = SensorReading(
        bin_id=reading_data.bin_id,
        fill_level_percent=reading_data.fill_level_percent,
        temperature_celsius=reading_data.temperature_celsius,
        battery_percent=reading_data.battery_percent,
        timestamp=reading_data.timestamp or datetime.now()
    )
    
    db.add(new_reading)
    db.commit()
    db.refresh(new_reading)
    
    # Check for alerts
    alert_service = AlertService(db)
    alerts = alert_service.check_and_create_alerts(new_reading)
    
    response = new_reading.to_dict()
    response['alerts_created'] = [a.id for a in alerts]
    
    return response


@router.post("/batch", response_model=dict)
def create_readings_batch(readings: List[SensorReadingCreate], db: Session = Depends(get_db)):
    """Submit multiple sensor readings at once"""
    created = []
    errors = []
    
    alert_service = AlertService(db)
    
    for reading_data in readings:
        try:
            # Verify bin exists
            bin_obj = db.query(WasteBin).filter(WasteBin.id == reading_data.bin_id).first()
            if not bin_obj:
                errors.append({"bin_id": reading_data.bin_id, "error": "Bin not found"})
                continue
            
            # Create reading
            new_reading = SensorReading(
                bin_id=reading_data.bin_id,
                fill_level_percent=reading_data.fill_level_percent,
                temperature_celsius=reading_data.temperature_celsius,
                battery_percent=reading_data.battery_percent,
                timestamp=reading_data.timestamp or datetime.now()
            )
            
            db.add(new_reading)
            db.flush()  # Flush to get ID without committing
            
            # Check for alerts
            alerts = alert_service.check_and_create_alerts(new_reading)
            
            created.append({
                "reading_id": new_reading.id,
                "bin_id": new_reading.bin_id,
                "alerts": [a.id for a in alerts]
            })
            
        except Exception as e:
            errors.append({"bin_id": reading_data.bin_id, "error": str(e)})
    
    db.commit()
    
    return {
        "created_count": len(created),
        "error_count": len(errors),
        "created": created,
        "errors": errors
    }


@router.get("/stats/hourly", response_model=List[dict])
def get_hourly_stats(
    bin_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get hourly average fill levels"""
    from sqlalchemy import func, extract
    
    since = datetime.now() - timedelta(hours=hours)
    
    query = db.query(
        extract('hour', SensorReading.timestamp).label('hour'),
        func.avg(SensorReading.fill_level_percent).label('avg_fill'),
        func.count(SensorReading.id).label('count')
    ).filter(SensorReading.timestamp >= since)
    
    if bin_id:
        query = query.filter(SensorReading.bin_id == bin_id)
    
    results = query.group_by(extract('hour', SensorReading.timestamp)).all()
    
    return [
        {
            "hour": int(r.hour),
            "avg_fill_level": round(r.avg_fill or 0, 2),
            "reading_count": r.count
        }
        for r in results
    ]
