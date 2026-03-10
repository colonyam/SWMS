"""Collection Routes API Router"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.collection_route import CollectionRoute, RouteStatus
from app.services.route_service import RouteService
from app.utils.schemas import (
    CollectionRouteCreate, CollectionRouteUpdate, 
    CollectionRouteResponse, RouteOptimizationRequest
)

router = APIRouter(prefix="/routes", tags=["Collection Routes"])


@router.get("/", response_model=List[CollectionRouteResponse])
def get_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all collection routes with optional filtering"""
    service = RouteService(db)
    routes = service.get_routes(skip=skip, limit=limit, status=status)
    
    return [r.to_dict() for r in routes]


@router.get("/{route_id}", response_model=CollectionRouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a specific route by ID"""
    service = RouteService(db)
    route = service.get_route_by_id(route_id)
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with ID {route_id} not found"
        )
    
    return route.to_dict()


@router.get("/{route_id}/stops")
def get_route_stops(route_id: int, db: Session = Depends(get_db)):
    """Get detailed stops for a route"""
    service = RouteService(db)
    stops = service.get_route_stops(route_id)
    
    return {
        "route_id": route_id,
        "stop_count": len(stops),
        "stops": stops
    }


@router.post("/", response_model=CollectionRouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(route_data: CollectionRouteCreate, db: Session = Depends(get_db)):
    """Create a new collection route"""
    service = RouteService(db)
    
    route_dict = route_data.model_dump()
    route = service.create_route(route_dict)
    
    return route.to_dict()


@router.put("/{route_id}", response_model=CollectionRouteResponse)
def update_route(route_id: int, route_data: CollectionRouteUpdate, db: Session = Depends(get_db)):
    """Update a collection route"""
    service = RouteService(db)
    
    route = service.update_route(route_id, route_data.model_dump(exclude_unset=True))
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with ID {route_id} not found"
        )
    
    return route.to_dict()


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: int, db: Session = Depends(get_db)):
    """Delete a collection route"""
    service = RouteService(db)
    success = service.delete_route(route_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with ID {route_id} not found"
        )
    
    return None


@router.post("/optimize")
def optimize_route(
    request: RouteOptimizationRequest,
    db: Session = Depends(get_db)
):
    """Generate an optimized collection route for given bins"""
    service = RouteService(db)
    
    result = service.optimize_route(
        bin_ids=request.bin_ids,
        start_location=request.start_location,
        vehicle_capacity=request.vehicle_capacity
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.post("/generate-smart")
def generate_smart_route(
    zone: Optional[str] = None,
    max_bins: int = Query(15, ge=2, le=50),
    min_fill_level: float = Query(60, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Automatically generate an optimized route based on current bin statuses"""
    service = RouteService(db)
    
    result = service.generate_smart_route(
        zone=zone,
        max_bins=max_bins,
        min_fill_level=min_fill_level
    )
    
    return result


@router.post("/{route_id}/start")
def start_route(route_id: int, db: Session = Depends(get_db)):
    """Mark route as in progress"""
    service = RouteService(db)
    route = service.start_route(route_id)
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with ID {route_id} not found"
        )
    
    return {
        "message": "Route started successfully",
        "route_id": route_id,
        "status": route.status.value
    }


@router.post("/{route_id}/complete")
def complete_route(route_id: int, db: Session = Depends(get_db)):
    """Mark route as completed and record collections"""
    service = RouteService(db)
    route = service.complete_route(route_id)
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with ID {route_id} not found"
        )
    
    return {
        "message": "Route completed successfully",
        "route_id": route_id,
        "status": route.status.value
    }


@router.get("/stats/summary")
def get_route_statistics(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """Get route performance statistics"""
    service = RouteService(db)
    return service.get_route_statistics(days=days)
