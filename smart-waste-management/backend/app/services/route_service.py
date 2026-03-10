"""Route Service - Route optimization and management"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import math
import logging

from app.models.waste_bin import WasteBin, BinStatus
from app.models.collection_route import CollectionRoute, RouteStatus
from app.models.collection_event import CollectionEvent
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert

logger = logging.getLogger(__name__)


class RouteService:
    """Service for collection route optimization and management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============== Route CRUD ==============
    
    def create_route(self, route_data: Dict) -> CollectionRoute:
        """Create a new collection route"""
        route = CollectionRoute(
            route_name=route_data.get("route_name"),
            vehicle_id=route_data.get("vehicle_id"),
            driver_name=route_data.get("driver_name"),
            scheduled_date=route_data.get("scheduled_date"),
            estimated_duration_minutes=route_data.get("estimated_duration_minutes"),
            total_distance_km=route_data.get("total_distance_km"),
            waypoints=route_data.get("waypoints", []),
            notes=route_data.get("notes"),
            status=RouteStatus.PLANNED
        )
        
        self.db.add(route)
        self.db.commit()
        self.db.refresh(route)
        
        logger.info(f"Created route: {route.route_name}")
        return route
    
    def get_route_by_id(self, route_id: int) -> Optional[CollectionRoute]:
        """Get a route by ID"""
        return self.db.query(CollectionRoute).filter(CollectionRoute.id == route_id).first()
    
    def get_routes(self, skip: int = 0, limit: int = 100, 
                   status: Optional[str] = None) -> List[CollectionRoute]:
        """Get routes with optional filtering"""
        query = self.db.query(CollectionRoute)
        
        if status:
            query = query.filter(CollectionRoute.status == status)
        
        return query.order_by(CollectionRoute.scheduled_date.desc()).offset(skip).limit(limit).all()
    
    def update_route(self, route_id: int, route_data: Dict) -> Optional[CollectionRoute]:
        """Update a route"""
        route = self.get_route_by_id(route_id)
        if not route:
            return None
        
        for key, value in route_data.items():
            if hasattr(route, key) and value is not None:
                setattr(route, key, value)
        
        route.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(route)
        
        logger.info(f"Updated route: {route.route_name}")
        return route
    
    def delete_route(self, route_id: int) -> bool:
        """Delete a route"""
        route = self.get_route_by_id(route_id)
        if not route:
            return False
        
        self.db.delete(route)
        self.db.commit()
        
        logger.info(f"Deleted route: {route_id}")
        return True
    
    # ============== Route Optimization ==============
    
    def optimize_route(self, bin_ids: List[int], 
                       start_location: Optional[Tuple[float, float]] = None,
                       vehicle_capacity: int = 5000) -> Dict:
        """Generate an optimized collection route using nearest neighbor algorithm"""
        
        # Get bin details
        bins = self.db.query(WasteBin).filter(
            WasteBin.id.in_(bin_ids),
            WasteBin.status == BinStatus.ACTIVE
        ).all()
        
        if not bins:
            return {"error": "No valid bins found for routing"}
        
        # Get current fill levels
        bin_data = []
        for bin_obj in bins:
            latest = self.db.query(SensorReading).filter(
                SensorReading.bin_id == bin_obj.id
            ).order_by(SensorReading.timestamp.desc()).first()
            
            fill_level = latest.fill_level_percent if latest else 0
            
            # Only include bins that need collection (>50% full)
            if fill_level >= 50:
                bin_data.append({
                    "id": bin_obj.id,
                    "location": bin_obj.location_name,
                    "lat": bin_obj.latitude,
                    "lon": bin_obj.longitude,
                    "fill_level": fill_level,
                    "capacity": bin_obj.capacity_liters
                })
        
        if len(bin_data) < 2:
            return {"error": "Need at least 2 bins with >50% fill level for optimization"}
        
        # Sort by fill level (highest first - priority)
        bin_data.sort(key=lambda x: x["fill_level"], reverse=True)
        
        # Determine start point
        if start_location:
            start_lat, start_lon = start_location
        else:
            # Use first bin as start
            start_lat, start_lon = bin_data[0]["lat"], bin_data[0]["lon"]
        
        # Nearest neighbor algorithm for route optimization
        optimized_order = self._nearest_neighbor_tsp(bin_data, start_lat, start_lon)
        
        # Calculate route metrics
        total_distance = self._calculate_route_distance(optimized_order)
        estimated_duration = self._estimate_route_duration(optimized_order, total_distance)
        
        # Generate route geometry (simplified - just connecting points)
        route_geometry = [(b["lat"], b["lon"]) for b in optimized_order]
        
        return {
            "optimized_order": [b["id"] for b in optimized_order],
            "waypoint_details": [
                {
                    "bin_id": b["id"],
                    "location": b["location"],
                    "fill_level": b["fill_level"],
                    "coordinates": [b["lat"], b["lon"]]
                }
                for b in optimized_order
            ],
            "estimated_distance_km": round(total_distance, 2),
            "estimated_duration_minutes": int(estimated_duration),
            "total_bins": len(optimized_order),
            "total_volume_liters": sum(b["capacity"] * (b["fill_level"] / 100) for b in optimized_order),
            "route_geometry": route_geometry
        }
    
    def _nearest_neighbor_tsp(self, bins: List[Dict], start_lat: float, 
                              start_lon: float) -> List[Dict]:
        """Simple nearest neighbor algorithm for TSP"""
        unvisited = bins.copy()
        route = []
        
        # Start from the closest bin to start location
        current_lat, current_lon = start_lat, start_lon
        
        while unvisited:
            # Find nearest unvisited bin
            nearest = min(unvisited, key=lambda b: self._haversine_distance(
                current_lat, current_lon, b["lat"], b["lon"]
            ))
            
            route.append(nearest)
            unvisited.remove(nearest)
            current_lat, current_lon = nearest["lat"], nearest["lon"]
        
        return route
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_route_distance(self, waypoints: List[Dict]) -> float:
        """Calculate total route distance"""
        if len(waypoints) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(waypoints) - 1):
            total_distance += self._haversine_distance(
                waypoints[i]["lat"], waypoints[i]["lon"],
                waypoints[i + 1]["lat"], waypoints[i + 1]["lon"]
            )
        
        return total_distance
    
    def _estimate_route_duration(self, waypoints: List[Dict], 
                                  distance_km: float) -> float:
        """Estimate route duration in minutes"""
        # Assume average speed of 30 km/h in urban areas
        driving_time = (distance_km / 30) * 60
        
        # Add collection time per bin (5 minutes per bin)
        collection_time = len(waypoints) * 5
        
        return driving_time + collection_time
    
    # ============== Smart Route Generation ==============
    
    def generate_smart_route(self, zone: Optional[str] = None,
                            max_bins: int = 15,
                            min_fill_level: float = 60) -> Dict:
        """Automatically generate an optimized route based on current bin statuses"""
        
        # Get bins that need collection
        query = self.db.query(WasteBin).filter(WasteBin.status == BinStatus.ACTIVE)
        
        if zone:
            query = query.filter(WasteBin.location_name.like(f"{zone}%"))
        
        bins = query.all()
        
        # Filter bins by fill level
        bins_needing_collection = []
        for bin_obj in bins:
            latest = self.db.query(SensorReading).filter(
                SensorReading.bin_id == bin_obj.id
            ).order_by(SensorReading.timestamp.desc()).first()
            
            fill_level = latest.fill_level_percent if latest else 0
            
            if fill_level >= min_fill_level:
                bins_needing_collection.append(bin_obj.id)
        
        # Limit to max bins
        if len(bins_needing_collection) > max_bins:
            # Sort by fill level and take top ones
            bins_with_levels = []
            for bin_id in bins_needing_collection:
                latest = self.db.query(SensorReading).filter(
                    SensorReading.bin_id == bin_id
                ).order_by(SensorReading.timestamp.desc()).first()
                
                bins_with_levels.append((bin_id, latest.fill_level_percent if latest else 0))
            
            bins_with_levels.sort(key=lambda x: x[1], reverse=True)
            bins_needing_collection = [b[0] for b in bins_with_levels[:max_bins]]
        
        if len(bins_needing_collection) < 2:
            return {
                "message": "Not enough bins need collection at this time",
                "bins_considered": len(bins_needing_collection),
                "recommended_action": "Wait for more bins to fill up"
            }
        
        # Optimize route
        return self.optimize_route(bins_needing_collection)
    
    # ============== Route Execution ==============
    
    def start_route(self, route_id: int) -> Optional[CollectionRoute]:
        """Mark route as in progress"""
        route = self.get_route_by_id(route_id)
        if not route:
            return None
        
        route.status = RouteStatus.IN_PROGRESS
        route.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"Route {route_id} started")
        return route
    
    def complete_route(self, route_id: int) -> Optional[CollectionRoute]:
        """Mark route as completed and record collections"""
        route = self.get_route_by_id(route_id)
        if not route:
            return None
        
        route.status = RouteStatus.COMPLETED
        route.updated_at = datetime.now()
        
        # Record collection events for all bins in route
        if route.waypoints:
            for bin_id in route.waypoints:
                # Get current fill level
                latest = self.db.query(SensorReading).filter(
                    SensorReading.bin_id == bin_id
                ).order_by(SensorReading.timestamp.desc()).first()
                
                collection_event = CollectionEvent(
                    bin_id=bin_id,
                    route_id=route_id,
                    collected_at=datetime.now(),
                    fill_level_at_collection=latest.fill_level_percent if latest else None,
                    notes=f"Collected as part of route: {route.route_name}"
                )
                self.db.add(collection_event)
        
        self.db.commit()
        logger.info(f"Route {route_id} completed")
        return route
    
    # ============== Route Statistics ==============
    
    def get_route_statistics(self, days: int = 30) -> Dict:
        """Get route performance statistics"""
        since = datetime.now() - timedelta(days=days)
        
        # Total routes
        total_routes = self.db.query(CollectionRoute).filter(
            CollectionRoute.created_at >= since
        ).count()
        
        # By status
        completed = self.db.query(CollectionRoute).filter(
            and_(
                CollectionRoute.status == RouteStatus.COMPLETED,
                CollectionRoute.created_at >= since
            )
        ).count()
        
        in_progress = self.db.query(CollectionRoute).filter(
            CollectionRoute.status == RouteStatus.IN_PROGRESS
        ).count()
        
        # Average distance and duration for completed routes
        completed_routes = self.db.query(CollectionRoute).filter(
            and_(
                CollectionRoute.status == RouteStatus.COMPLETED,
                CollectionRoute.created_at >= since
            )
        ).all()
        
        if completed_routes:
            avg_distance = sum(r.total_distance_km or 0 for r in completed_routes) / len(completed_routes)
            avg_duration = sum(r.estimated_duration_minutes or 0 for r in completed_routes) / len(completed_routes)
        else:
            avg_distance = 0
            avg_duration = 0
        
        return {
            "period_days": days,
            "total_routes": total_routes,
            "completed_routes": completed,
            "in_progress_routes": in_progress,
            "completion_rate": round((completed / total_routes * 100), 2) if total_routes > 0 else 0,
            "avg_distance_km": round(avg_distance, 2),
            "avg_duration_minutes": round(avg_duration, 2)
        }
    
    def get_route_stops(self, route_id: int) -> List[Dict]:
        """Get detailed stops for a route"""
        route = self.get_route_by_id(route_id)
        if not route or not route.waypoints:
            return []
        
        stops = []
        for i, bin_id in enumerate(route.waypoints):
            bin_obj = self.db.query(WasteBin).filter(WasteBin.id == bin_id).first()
            if not bin_obj:
                continue
            
            # Get current fill level
            latest = self.db.query(SensorReading).filter(
                SensorReading.bin_id == bin_id
            ).order_by(SensorReading.timestamp.desc()).first()
            
            # Check if collected
            collection = self.db.query(CollectionEvent).filter(
                and_(
                    CollectionEvent.bin_id == bin_id,
                    CollectionEvent.route_id == route_id
                )
            ).first()
            
            stops.append({
                "stop_number": i + 1,
                "bin_id": bin_id,
                "location": bin_obj.location_name,
                "coordinates": [bin_obj.latitude, bin_obj.longitude],
                "fill_level": latest.fill_level_percent if latest else 0,
                "collected": collection is not None,
                "collected_at": collection.collected_at.isoformat() if collection else None
            })
        
        return stops
