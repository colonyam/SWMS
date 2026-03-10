"""Alerts API Router"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.alert import Alert, AlertType, AlertSeverity
from app.services.alert_service import AlertService
from app.utils.schemas import AlertResponse, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    bin_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering"""
    service = AlertService(db)
    alerts = service.get_alerts(
        skip=skip, limit=limit,
        alert_type=alert_type,
        severity=severity,
        is_resolved=is_resolved,
        bin_id=bin_id
    )
    
    return [a.to_dict() for a in alerts]


@router.get("/unresolved", response_model=List[AlertResponse])
def get_unresolved_alerts(
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all unresolved alerts"""
    service = AlertService(db)
    alerts = service.get_unresolved_alerts(severity=severity)
    
    return [a.to_dict() for a in alerts]


@router.get("/critical-count")
def get_critical_count(db: Session = Depends(get_db)):
    """Get count of critical unresolved alerts"""
    service = AlertService(db)
    count = service.get_critical_alerts_count()
    
    return {"critical_unresolved_count": count}


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert by ID"""
    service = AlertService(db)
    alert = service.get_alert_by_id(alert_id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    return alert.to_dict()


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    update_data: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Resolve an alert"""
    service = AlertService(db)
    
    alert = service.resolve_alert(
        alert_id=alert_id,
        resolved_by=update_data.resolved_by or "system",
        notes=update_data.resolution_notes
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    return alert.to_dict()


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert"""
    service = AlertService(db)
    success = service.delete_alert(alert_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found"
        )
    
    return None


@router.get("/stats/summary")
def get_alert_statistics(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get alert statistics summary"""
    service = AlertService(db)
    return service.get_alert_statistics(days=days)


@router.get("/check/offline-sensors")
def check_offline_sensors(
    threshold_minutes: int = Query(120, ge=30, le=1440),
    db: Session = Depends(get_db)
):
    """Check for sensors that haven't reported recently"""
    service = AlertService(db)
    offline_sensors = service.check_offline_sensors(threshold_minutes)
    
    return {
        "offline_count": len(offline_sensors),
        "threshold_minutes": threshold_minutes,
        "offline_sensors": offline_sensors
    }
