"""Analytics Service - Data processing and predictive analytics"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import logging

from app.models.waste_bin import WasteBin, BinStatus
from app.models.sensor_reading import SensorReading
from app.models.collection_event import CollectionEvent
from app.models.alert import Alert

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for waste management analytics and predictions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============== Dashboard Statistics ==============
    
    def get_dashboard_stats(self) -> Dict:
        """Get comprehensive dashboard statistics"""
        try:
            # Bin counts
            total_bins = self.db.query(WasteBin).count()
            active_bins = self.db.query(WasteBin).filter(WasteBin.status == BinStatus.ACTIVE).count()
            maintenance_bins = self.db.query(WasteBin).filter(WasteBin.status == BinStatus.MAINTENANCE).count()
            
            # Get latest readings for fill level analysis
            latest_readings = self._get_latest_readings_for_all_bins()
            
            critical_bins = sum(1 for r in latest_readings if r['fill_level_percent'] >= 95)
            high_fill_bins = sum(1 for r in latest_readings if 80 <= r['fill_level_percent'] < 95)
            
            avg_fill = np.mean([r['fill_level_percent'] for r in latest_readings]) if latest_readings else 0
            
            # Today's collections
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            collections_today = self.db.query(CollectionEvent).filter(
                CollectionEvent.collected_at >= today_start
            ).count()
            
            # Unresolved alerts
            unresolved_alerts = self.db.query(Alert).filter(Alert.is_resolved == False).count()
            
            return {
                "total_bins": total_bins,
                "active_bins": active_bins,
                "maintenance_bins": maintenance_bins,
                "critical_bins": critical_bins,
                "high_fill_bins": high_fill_bins,
                "avg_fill_level": round(avg_fill, 2),
                "total_collections_today": collections_today,
                "unresolved_alerts": unresolved_alerts,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self) -> Dict:
        """Return default stats when error occurs"""
        return {
            "total_bins": 0,
            "active_bins": 0,
            "maintenance_bins": 0,
            "critical_bins": 0,
            "high_fill_bins": 0,
            "avg_fill_level": 0,
            "total_collections_today": 0,
            "unresolved_alerts": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_latest_readings_for_all_bins(self) -> List[Dict]:
        """Get the most recent reading for each bin"""
        # Subquery to get latest timestamp per bin
        subquery = self.db.query(
            SensorReading.bin_id,
            func.max(SensorReading.timestamp).label('max_time')
        ).group_by(SensorReading.bin_id).subquery()
        
        # Join to get full reading data
        readings = self.db.query(SensorReading).join(
            subquery,
            and_(
                SensorReading.bin_id == subquery.c.bin_id,
                SensorReading.timestamp == subquery.c.max_time
            )
        ).all()
        
        return [r.to_dict() for r in readings]
    
    # ============== Fill Pattern Analysis ==============
    
    def get_fill_patterns(self, bin_id: Optional[int] = None, days: int = 7) -> List[Dict]:
        """Analyze fill patterns for bins"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            # Query bins to analyze
            bins_query = self.db.query(WasteBin)
            if bin_id:
                bins_query = bins_query.filter(WasteBin.id == bin_id)
            bins = bins_query.all()
            
            results = []
            for bin_obj in bins:
                pattern = self._analyze_single_bin_pattern(bin_obj.id, since)
                if pattern:
                    results.append(pattern)
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing fill patterns: {e}")
            return []
    
    def _analyze_single_bin_pattern(self, bin_id: int, since: datetime) -> Optional[Dict]:
        """Analyze fill pattern for a single bin"""
        readings = self.db.query(SensorReading).filter(
            SensorReading.bin_id == bin_id,
            SensorReading.timestamp >= since
        ).order_by(SensorReading.timestamp).all()
        
        if len(readings) < 5:
            return None
        
        bin_obj = self.db.query(WasteBin).filter(WasteBin.id == bin_id).first()
        if not bin_obj:
            return None
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'timestamp': r.timestamp,
            'fill_level': r.fill_level_percent
        } for r in readings])
        
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Hourly averages
        hourly_avg = df.groupby('hour')['fill_level'].mean().reindex(range(24), fill_value=0).tolist()
        
        # Daily averages
        daily_avg = df.groupby('day_of_week')['fill_level'].mean().reindex(range(7), fill_value=0).tolist()
        
        # Trend analysis
        trend = self._calculate_trend(df)
        
        return {
            "bin_id": bin_id,
            "bin_location": bin_obj.location_name,
            "hourly_avg": [round(x, 2) for x in hourly_avg],
            "daily_avg": [round(x, 2) for x in daily_avg],
            "trend": trend
        }
    
    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """Calculate trend direction from DataFrame"""
        if len(df) < 10:
            return "stable"
        
        # Simple linear regression on fill levels
        x = np.arange(len(df)).reshape(-1, 1)
        y = df['fill_level'].values
        
        model = LinearRegression()
        model.fit(x, y)
        slope = model.coef_[0]
        
        if slope > 0.5:
            return "increasing"
        elif slope < -0.5:
            return "decreasing"
        return "stable"
    
    # ============== Predictive Analytics ==============
    
    def get_fill_predictions(self, bin_id: Optional[int] = None) -> List[Dict]:
        """Predict future fill levels for bins"""
        try:
            bins_query = self.db.query(WasteBin)
            if bin_id:
                bins_query = bins_query.filter(WasteBin.id == bin_id)
            bins = bins_query.all()
            
            results = []
            for bin_obj in bins:
                prediction = self._predict_single_bin(bin_obj)
                if prediction:
                    results.append(prediction)
            
            return results
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return []
    
    def _predict_single_bin(self, bin_obj: WasteBin) -> Optional[Dict]:
        """Generate fill prediction for a single bin"""
        # Get last 14 days of readings
        since = datetime.now() - timedelta(days=14)
        readings = self.db.query(SensorReading).filter(
            SensorReading.bin_id == bin_obj.id,
            SensorReading.timestamp >= since
        ).order_by(SensorReading.timestamp).all()
        
        if len(readings) < 10:
            return None
        
        current_fill = readings[-1].fill_level_percent
        
        # Prepare data for prediction
        df = pd.DataFrame([{
            'timestamp': r.timestamp,
            'fill_level': r.fill_level_percent,
            'hour': r.timestamp.hour,
            'day_of_week': r.timestamp.weekday()
        } for r in readings])
        
        # Calculate fill rate (percent per hour)
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
        df['fill_diff'] = df['fill_level'].diff()
        df['fill_rate'] = df['fill_diff'] / df['time_diff']
        
        # Average fill rate (excluding negative values - collections)
        avg_fill_rate = df[df['fill_rate'] > 0]['fill_rate'].mean()
        
        if pd.isna(avg_fill_rate) or avg_fill_rate <= 0:
            avg_fill_rate = 0.5  # Default assumption
        
        # Predictions
        hours_24 = 24
        hours_7d = 24 * 7
        
        predicted_24h = min(100, current_fill + (avg_fill_rate * hours_24))
        predicted_7d = min(100, current_fill + (avg_fill_rate * hours_7d))
        
        # Calculate recommended collection time
        hours_to_full = (95 - current_fill) / avg_fill_rate if avg_fill_rate > 0 else float('inf')
        recommended_time = datetime.now() + timedelta(hours=hours_to_full) if hours_to_full < 168 else None
        
        # Confidence based on data quality
        confidence = min(0.95, 0.5 + (len(readings) / 200))
        
        return {
            "bin_id": bin_obj.id,
            "bin_location": bin_obj.location_name,
            "current_fill": round(current_fill, 2),
            "predicted_fill_24h": round(predicted_24h, 2),
            "predicted_fill_7d": round(predicted_7d, 2),
            "recommended_collection_time": recommended_time.isoformat() if recommended_time else None,
            "confidence_score": round(confidence, 2)
        }
    
    # ============== Efficiency Metrics ==============
    
    def get_efficiency_metrics(self, days: int = 30) -> Dict:
        """Calculate collection efficiency metrics"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            # Total collections in period
            total_collections = self.db.query(CollectionEvent).filter(
                CollectionEvent.collected_at >= since
            ).count()
            
            if total_collections == 0:
                return self._get_default_efficiency_metrics(days)
            
            # Average fill level at collection
            avg_fill_result = self.db.query(
                func.avg(CollectionEvent.fill_level_at_collection)
            ).filter(CollectionEvent.collected_at >= since).first()
            
            avg_fill_at_collection = avg_fill_result[0] if avg_fill_result[0] else 0
            
            # Collections per day
            collections_per_day = total_collections / days
            
            # Calculate efficiency score (higher fill at collection = better)
            # Ideal is collecting at 85-95% full
            efficiency_score = min(100, (avg_fill_at_collection / 85) * 100) if avg_fill_at_collection > 0 else 0
            
            # Estimate cost savings (assuming 20% improvement potential)
            cost_savings = max(0, (efficiency_score - 60)) * 0.5
            
            return {
                "period_days": days,
                "total_collections": total_collections,
                "avg_fill_at_collection": round(avg_fill_at_collection, 2),
                "collections_per_day": round(collections_per_day, 2),
                "fuel_efficiency_score": round(efficiency_score, 2),
                "cost_savings_percent": round(cost_savings, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {e}")
            return self._get_default_efficiency_metrics(days)
    
    def _get_default_efficiency_metrics(self, days: int) -> Dict:
        """Return default efficiency metrics"""
        return {
            "period_days": days,
            "total_collections": 0,
            "avg_fill_at_collection": 0,
            "collections_per_day": 0,
            "fuel_efficiency_score": 0,
            "cost_savings_percent": 0
        }
    
    # ============== Zone Analysis ==============
    
    def get_zone_analysis(self) -> List[Dict]:
        """Analyze waste generation by zone/area"""
        try:
            # Group bins by general area (simplified - using first word of location)
            bins = self.db.query(WasteBin).all()
            
            zones = {}
            for bin_obj in bins:
                # Extract zone from location name (first word)
                zone = bin_obj.location_name.split()[0] if bin_obj.location_name else "Unknown"
                
                if zone not in zones:
                    zones[zone] = {"bins": [], "total_fill": 0, "count": 0}
                
                # Get latest reading
                latest = self.db.query(SensorReading).filter(
                    SensorReading.bin_id == bin_obj.id
                ).order_by(desc(SensorReading.timestamp)).first()
                
                fill_level = latest.fill_level_percent if latest else 0
                zones[zone]["bins"].append(bin_obj.id)
                zones[zone]["total_fill"] += fill_level
                zones[zone]["count"] += 1
            
            # Calculate averages and format results
            results = []
            for zone_name, data in zones.items():
                avg_fill = data["total_fill"] / data["count"] if data["count"] > 0 else 0
                results.append({
                    "zone": zone_name,
                    "bin_count": data["count"],
                    "avg_fill_level": round(avg_fill, 2),
                    "priority": "high" if avg_fill > 80 else "medium" if avg_fill > 50 else "low"
                })
            
            return sorted(results, key=lambda x: x["avg_fill_level"], reverse=True)
        except Exception as e:
            logger.error(f"Error in zone analysis: {e}")
            return []
    
    # ============== Historical Data ==============
    
    def get_historical_data(self, metric: str, days: int = 30) -> List[Dict]:
        """Get historical data for charts"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            if metric == "fill_levels":
                return self._get_historical_fill_levels(since)
            elif metric == "collections":
                return self._get_historical_collections(since)
            elif metric == "alerts":
                return self._get_historical_alerts(since)
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def _get_historical_fill_levels(self, since: datetime) -> List[Dict]:
        """Get average fill levels over time"""
        readings = self.db.query(
            func.date(SensorReading.timestamp).label('date'),
            func.avg(SensorReading.fill_level_percent).label('avg_fill')
        ).filter(SensorReading.timestamp >= since).group_by(
            func.date(SensorReading.timestamp)
        ).all()
        
        return [
            {"date": str(r.date), "value": round(r.avg_fill or 0, 2)}
            for r in readings
        ]
    
    def _get_historical_collections(self, since: datetime) -> List[Dict]:
        """Get collection counts over time"""
        collections = self.db.query(
            func.date(CollectionEvent.collected_at).label('date'),
            func.count(CollectionEvent.id).label('count')
        ).filter(CollectionEvent.collected_at >= since).group_by(
            func.date(CollectionEvent.collected_at)
        ).all()
        
        return [
            {"date": str(c.date), "value": c.count}
            for c in collections
        ]
    
    def _get_historical_alerts(self, since: datetime) -> List[Dict]:
        """Get alert counts over time"""
        alerts = self.db.query(
            func.date(Alert.created_at).label('date'),
            func.count(Alert.id).label('count')
        ).filter(Alert.created_at >= since).group_by(
            func.date(Alert.created_at)
        ).all()
        
        return [
            {"date": str(a.date), "value": a.count}
            for a in alerts
        ]
