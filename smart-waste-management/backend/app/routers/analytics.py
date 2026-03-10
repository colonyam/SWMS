"""Analytics API Router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics"""
    service = AnalyticsService(db)
    return service.get_dashboard_stats()


@router.get("/fill-patterns")
def get_fill_patterns(
    bin_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Analyze fill patterns for bins"""
    service = AnalyticsService(db)
    return service.get_fill_patterns(bin_id=bin_id, days=days)


@router.get("/predictions")
def get_predictions(
    bin_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get fill level predictions for bins"""
    service = AnalyticsService(db)
    return service.get_fill_predictions(bin_id=bin_id)


@router.get("/efficiency")
def get_efficiency_metrics(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """Get collection efficiency metrics"""
    service = AnalyticsService(db)
    return service.get_efficiency_metrics(days=days)


@router.get("/zones")
def get_zone_analysis(db: Session = Depends(get_db)):
    """Analyze waste generation by zones"""
    service = AnalyticsService(db)
    return service.get_zone_analysis()


@router.get("/historical/{metric}")
def get_historical_data(
    metric: str,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """Get historical data for charts
    
    Available metrics:
    - fill_levels: Average fill levels over time
    - collections: Collection counts over time
    - alerts: Alert counts over time
    """
    service = AnalyticsService(db)
    return service.get_historical_data(metric, days=days)


@router.get("/bins/status-distribution")
def get_bin_status_distribution(db: Session = Depends(get_db)):
    """Get distribution of bins by fill level ranges"""
    from sqlalchemy import func, case
    from app.models.sensor_reading import SensorReading
    from app.models.waste_bin import WasteBin
    
    # Get latest readings for all bins
    subquery = db.query(
        SensorReading.bin_id,
        func.max(SensorReading.timestamp).label('max_time')
    ).group_by(SensorReading.bin_id).subquery()
    
    readings = db.query(SensorReading).join(
        subquery,
        (SensorReading.bin_id == subquery.c.bin_id) &
        (SensorReading.timestamp == subquery.c.max_time)
    ).all()
    
    # Categorize by fill level
    critical = sum(1 for r in readings if r.fill_level_percent >= 95)
    high = sum(1 for r in readings if 80 <= r.fill_level_percent < 95)
    medium = sum(1 for r in readings if 50 <= r.fill_level_percent < 80)
    low = sum(1 for r in readings if 20 <= r.fill_level_percent < 50)
    empty = sum(1 for r in readings if r.fill_level_percent < 20)
    
    # Bins with no readings
    total_bins = db.query(WasteBin).count()
    no_data = total_bins - len(readings)
    
    return {
        "critical_95_100": critical,
        "high_80_95": high,
        "medium_50_80": medium,
        "low_20_50": low,
        "empty_0_20": empty,
        "no_data": no_data,
        "total_bins": total_bins
    }


@router.get("/bins/fill-trends")
def get_fill_trends(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get daily average fill level trends"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app.models.sensor_reading import SensorReading
    
    since = datetime.now() - timedelta(days=days)
    
    results = db.query(
        func.date(SensorReading.timestamp).label('date'),
        func.avg(SensorReading.fill_level_percent).label('avg_fill'),
        func.count(SensorReading.id).label('reading_count')
    ).filter(
        SensorReading.timestamp >= since
    ).group_by(
        func.date(SensorReading.timestamp)
    ).order_by('date').all()
    
    return [
        {
            "date": str(r.date),
            "avg_fill_level": round(r.avg_fill or 0, 2),
            "reading_count": r.reading_count
        }
        for r in results
    ]


@router.get("/collections/by-type")
def get_collections_by_type(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get collection statistics by bin type"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app.models.collection_event import CollectionEvent
    from app.models.waste_bin import WasteBin
    
    since = datetime.now() - timedelta(days=days)
    
    results = db.query(
        WasteBin.bin_type,
        func.count(CollectionEvent.id).label('collection_count'),
        func.avg(CollectionEvent.fill_level_at_collection).label('avg_fill_at_collection')
    ).join(
        CollectionEvent, WasteBin.id == CollectionEvent.bin_id
    ).filter(
        CollectionEvent.collected_at >= since
    ).group_by(
        WasteBin.bin_type
    ).all()
    
    return [
        {
            "bin_type": r.bin_type.value,
            "collection_count": r.collection_count,
            "avg_fill_at_collection": round(r.avg_fill_at_collection or 0, 2)
        }
        for r in results
    ]
