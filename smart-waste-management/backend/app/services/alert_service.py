"""Alert Service - Alert management and notifications"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

from app.models.alert import Alert, AlertType, AlertSeverity
from app.models.waste_bin import WasteBin
from app.models.sensor_reading import SensorReading
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertService:
    """Service for managing waste management alerts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============== Alert Creation ==============
    
    def check_and_create_alerts(self, reading: SensorReading) -> List[Alert]:
        """Check sensor reading and create appropriate alerts"""
        created_alerts = []
        
        # Check fill level
        fill_alert = self._check_fill_level(reading)
        if fill_alert:
            created_alerts.append(fill_alert)
        
        # Check battery level
        battery_alert = self._check_battery_level(reading)
        if battery_alert:
            created_alerts.append(battery_alert)
        
        return created_alerts
    
    def _check_fill_level(self, reading: SensorReading) -> Optional[Alert]:
        """Check if fill level triggers an alert"""
        fill_level = reading.fill_level_percent
        
        if fill_level >= settings.ALERT_FILL_THRESHOLD_CRITICAL:
            # Check if unresolved critical alert already exists
            existing = self.db.query(Alert).filter(
                and_(
                    Alert.bin_id == reading.bin_id,
                    Alert.alert_type == AlertType.FILL_LEVEL_CRITICAL,
                    Alert.is_resolved == False
                )
            ).first()
            
            if not existing:
                return self._create_alert(
                    bin_id=reading.bin_id,
                    alert_type=AlertType.FILL_LEVEL_CRITICAL,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Bin is critically full ({fill_level:.1f}%). Immediate collection required."
                )
        
        elif fill_level >= settings.ALERT_FILL_THRESHOLD_HIGH:
            # Check if unresolved high alert already exists
            existing = self.db.query(Alert).filter(
                and_(
                    Alert.bin_id == reading.bin_id,
                    Alert.alert_type == AlertType.FILL_LEVEL_HIGH,
                    Alert.is_resolved == False
                )
            ).first()
            
            if not existing:
                return self._create_alert(
                    bin_id=reading.bin_id,
                    alert_type=AlertType.FILL_LEVEL_HIGH,
                    severity=AlertSeverity.HIGH,
                    message=f"Bin fill level is high ({fill_level:.1f}%). Schedule collection soon."
                )
        
        return None
    
    def _check_battery_level(self, reading: SensorReading) -> Optional[Alert]:
        """Check if battery level triggers an alert"""
        battery = reading.battery_percent
        
        if battery <= settings.ALERT_BATTERY_THRESHOLD:
            # Check if unresolved battery alert already exists
            existing = self.db.query(Alert).filter(
                and_(
                    Alert.bin_id == reading.bin_id,
                    Alert.alert_type == AlertType.LOW_BATTERY,
                    Alert.is_resolved == False
                )
            ).first()
            
            if not existing:
                return self._create_alert(
                    bin_id=reading.bin_id,
                    alert_type=AlertType.LOW_BATTERY,
                    severity=AlertSeverity.MEDIUM,
                    message=f"Sensor battery is low ({battery:.1f}%). Replace or recharge soon."
                )
        
        return None
    
    def _create_alert(self, bin_id: int, alert_type: AlertType, 
                      severity: AlertSeverity, message: str) -> Alert:
        """Create a new alert"""
        alert = Alert(
            bin_id=bin_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            is_resolved=False,
            created_at=datetime.now()
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Created alert: {alert_type.value} for bin {bin_id}")
        return alert
    
    # ============== Alert Management ==============
    
    def get_alerts(self, skip: int = 0, limit: int = 100, 
                   alert_type: Optional[str] = None,
                   severity: Optional[str] = None,
                   is_resolved: Optional[bool] = None,
                   bin_id: Optional[int] = None) -> List[Alert]:
        """Get alerts with optional filtering"""
        query = self.db.query(Alert)
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if severity:
            query = query.filter(Alert.severity == severity)
        if is_resolved is not None:
            query = query.filter(Alert.is_resolved == is_resolved)
        if bin_id:
            query = query.filter(Alert.bin_id == bin_id)
        
        return query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
    
    def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        """Get a single alert by ID"""
        return self.db.query(Alert).filter(Alert.id == alert_id).first()
    
    def get_unresolved_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Get all unresolved alerts, optionally filtered by severity"""
        query = self.db.query(Alert).filter(Alert.is_resolved == False)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        return query.order_by(desc(Alert.created_at)).all()
    
    def get_critical_alerts_count(self) -> int:
        """Get count of critical unresolved alerts"""
        return self.db.query(Alert).filter(
            and_(
                Alert.is_resolved == False,
                Alert.severity == AlertSeverity.CRITICAL
            )
        ).count()
    
    # ============== Alert Resolution ==============
    
    def resolve_alert(self, alert_id: int, resolved_by: str, 
                      notes: Optional[str] = None) -> Optional[Alert]:
        """Resolve an alert"""
        alert = self.get_alert_by_id(alert_id)
        
        if not alert:
            return None
        
        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        alert.resolved_by = resolved_by
        alert.resolution_notes = notes
        
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Resolved alert {alert_id} by {resolved_by}")
        return alert
    
    def resolve_alerts_for_bin(self, bin_id: int, resolved_by: str = "system") -> int:
        """Resolve all unresolved alerts for a bin (e.g., after collection)"""
        alerts = self.db.query(Alert).filter(
            and_(
                Alert.bin_id == bin_id,
                Alert.is_resolved == False
            )
        ).all()
        
        resolved_count = 0
        for alert in alerts:
            alert.is_resolved = True
            alert.resolved_at = datetime.now()
            alert.resolved_by = resolved_by
            alert.resolution_notes = "Automatically resolved after collection"
            resolved_count += 1
        
        if resolved_count > 0:
            self.db.commit()
            logger.info(f"Resolved {resolved_count} alerts for bin {bin_id}")
        
        return resolved_count
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        alert = self.get_alert_by_id(alert_id)
        
        if not alert:
            return False
        
        self.db.delete(alert)
        self.db.commit()
        
        logger.info(f"Deleted alert {alert_id}")
        return True
    
    # ============== Alert Statistics ==============
    
    def get_alert_statistics(self, days: int = 30) -> Dict:
        """Get alert statistics for the given period"""
        since = datetime.now() - timedelta(days=days)
        
        # Total alerts
        total_alerts = self.db.query(Alert).filter(Alert.created_at >= since).count()
        
        # By type
        type_counts = {}
        for alert_type in AlertType:
            count = self.db.query(Alert).filter(
                and_(
                    Alert.alert_type == alert_type,
                    Alert.created_at >= since
                )
            ).count()
            type_counts[alert_type.value] = count
        
        # By severity
        severity_counts = {}
        for severity in AlertSeverity:
            count = self.db.query(Alert).filter(
                and_(
                    Alert.severity == severity,
                    Alert.created_at >= since
                )
            ).count()
            severity_counts[severity.value] = count
        
        # Unresolved by severity
        unresolved_critical = self.db.query(Alert).filter(
            and_(
                Alert.severity == AlertSeverity.CRITICAL,
                Alert.is_resolved == False
            )
        ).count()
        
        unresolved_high = self.db.query(Alert).filter(
            and_(
                Alert.severity == AlertSeverity.HIGH,
                Alert.is_resolved == False
            )
        ).count()
        
        # Average resolution time
        resolved_alerts = self.db.query(Alert).filter(
            and_(
                Alert.is_resolved == True,
                Alert.created_at >= since
            )
        ).all()
        
        if resolved_alerts:
            total_resolution_time = sum(
                (a.resolved_at - a.created_at).total_seconds() / 3600
                for a in resolved_alerts if a.resolved_at
            )
            avg_resolution_hours = total_resolution_time / len(resolved_alerts)
        else:
            avg_resolution_hours = 0
        
        return {
            "period_days": days,
            "total_alerts": total_alerts,
            "by_type": type_counts,
            "by_severity": severity_counts,
            "unresolved_critical": unresolved_critical,
            "unresolved_high": unresolved_high,
            "avg_resolution_hours": round(avg_resolution_hours, 2)
        }
    
    # ============== Sensor Offline Detection ==============
    
    def check_offline_sensors(self, offline_threshold_minutes: int = 120) -> List[Dict]:
        """Check for sensors that haven't reported in a while"""
        threshold_time = datetime.now() - timedelta(minutes=offline_threshold_minutes)
        
        # Get all active bins
        active_bins = self.db.query(WasteBin).filter(
            WasteBin.status == "active"
        ).all()
        
        offline_bins = []
        for bin_obj in active_bins:
            # Get latest reading
            latest = self.db.query(SensorReading).filter(
                SensorReading.bin_id == bin_obj.id
            ).order_by(desc(SensorReading.timestamp)).first()
            
            if not latest or latest.timestamp < threshold_time:
                offline_bins.append({
                    "bin_id": bin_obj.id,
                    "location": bin_obj.location_name,
                    "last_reading": latest.timestamp.isoformat() if latest else None,
                    "minutes_offline": int((datetime.now() - (latest.timestamp if latest else bin_obj.install_date)).total_seconds() / 60)
                })
                
                # Create alert if not exists
                existing = self.db.query(Alert).filter(
                    and_(
                        Alert.bin_id == bin_obj.id,
                        Alert.alert_type == AlertType.SENSOR_OFFLINE,
                        Alert.is_resolved == False
                    )
                ).first()
                
                if not existing:
                    self._create_alert(
                        bin_id=bin_obj.id,
                        alert_type=AlertType.SENSOR_OFFLINE,
                        severity=AlertSeverity.HIGH,
                        message=f"Sensor has not reported for {offline_threshold_minutes}+ minutes. Check connectivity."
                    )
        
        return offline_bins
