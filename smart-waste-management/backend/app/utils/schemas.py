"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============== Enums ==============
class BinTypeEnum(str, Enum):
    GENERAL = "general"
    RECYCLING = "recycling"
    ORGANIC = "organic"
    HAZARDOUS = "hazardous"


class BinStatusEnum(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class AlertTypeEnum(str, Enum):
    FILL_LEVEL_HIGH = "fill_level_high"
    FILL_LEVEL_CRITICAL = "fill_level_critical"
    LOW_BATTERY = "low_battery"
    SENSOR_OFFLINE = "sensor_offline"
    MAINTENANCE_REQUIRED = "maintenance_required"


class AlertSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RouteStatusEnum(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


# ============== User Schemas ==============
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRoleEnum = UserRoleEnum.OPERATOR


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role: UserRoleEnum
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


# ============== Waste Bin Schemas ==============
class WasteBinBase(BaseModel):
    location_name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    bin_type: BinTypeEnum = BinTypeEnum.GENERAL
    capacity_liters: int = Field(default=240, ge=50, le=2000)


class WasteBinCreate(WasteBinBase):
    pass


class WasteBinUpdate(BaseModel):
    location_name: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    bin_type: Optional[BinTypeEnum] = None
    capacity_liters: Optional[int] = Field(None, ge=50, le=2000)
    status: Optional[BinStatusEnum] = None


class WasteBinResponse(WasteBinBase):
    id: int
    status: BinStatusEnum
    install_date: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    latest_reading: Optional[dict] = None
    
    class Config:
        from_attributes = True


# ============== Sensor Reading Schemas ==============
class SensorReadingBase(BaseModel):
    bin_id: int
    fill_level_percent: float = Field(..., ge=0, le=100)
    temperature_celsius: Optional[float] = None
    battery_percent: float = Field(default=100.0, ge=0, le=100)


class SensorReadingCreate(SensorReadingBase):
    timestamp: Optional[datetime] = None


class SensorReadingResponse(SensorReadingBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class SensorReadingHistory(BaseModel):
    bin_id: int
    readings: List[SensorReadingResponse]
    total_count: int


# ============== Alert Schemas ==============
class AlertBase(BaseModel):
    bin_id: int
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    message: str


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    is_resolved: bool
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertResponse(AlertBase):
    id: int
    bin_location: Optional[str]
    is_resolved: bool
    created_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    
    class Config:
        from_attributes = True


# ============== Collection Route Schemas ==============
class CollectionRouteBase(BaseModel):
    route_name: str = Field(..., min_length=1, max_length=255)
    vehicle_id: Optional[str] = Field(None, max_length=50)
    driver_name: Optional[str] = Field(None, max_length=100)
    scheduled_date: datetime
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    total_distance_km: Optional[float] = Field(None, ge=0)
    waypoints: Optional[List[int]] = []
    notes: Optional[str] = None


class CollectionRouteCreate(CollectionRouteBase):
    pass


class CollectionRouteUpdate(BaseModel):
    route_name: Optional[str] = Field(None, min_length=1, max_length=255)
    vehicle_id: Optional[str] = Field(None, max_length=50)
    driver_name: Optional[str] = Field(None, max_length=100)
    scheduled_date: Optional[datetime] = None
    status: Optional[RouteStatusEnum] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    total_distance_km: Optional[float] = Field(None, ge=0)
    waypoints: Optional[List[int]] = None
    notes: Optional[str] = None


class CollectionRouteResponse(CollectionRouteBase):
    id: int
    status: RouteStatusEnum
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============== Collection Event Schemas ==============
class CollectionEventBase(BaseModel):
    bin_id: int
    route_id: Optional[int] = None
    fill_level_at_collection: Optional[float] = Field(None, ge=0, le=100)
    weight_kg: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class CollectionEventCreate(CollectionEventBase):
    collected_at: Optional[datetime] = None


class CollectionEventResponse(CollectionEventBase):
    id: int
    bin_location: Optional[str]
    collected_at: datetime
    
    class Config:
        from_attributes = True


# ============== Analytics Schemas ==============
class DashboardStats(BaseModel):
    total_bins: int
    active_bins: int
    maintenance_bins: int
    critical_bins: int
    high_fill_bins: int
    avg_fill_level: float
    total_collections_today: int
    unresolved_alerts: int


class FillPatternData(BaseModel):
    bin_id: int
    bin_location: str
    hourly_avg: List[float]
    daily_avg: List[float]
    trend: str  # "increasing", "decreasing", "stable"


class EfficiencyMetrics(BaseModel):
    period_days: int
    total_collections: int
    avg_fill_at_collection: float
    collections_per_day: float
    fuel_efficiency_score: float
    cost_savings_percent: float


class PredictionData(BaseModel):
    bin_id: int
    bin_location: str
    current_fill: float
    predicted_fill_24h: float
    predicted_fill_7d: float
    recommended_collection_time: datetime
    confidence_score: float


class RouteOptimizationRequest(BaseModel):
    bin_ids: List[int]
    start_location: Optional[tuple] = None  # (lat, lon)
    vehicle_capacity: Optional[int] = 5000
    max_route_time_minutes: Optional[int] = 480


class RouteOptimizationResponse(BaseModel):
    optimized_order: List[int]
    estimated_distance_km: float
    estimated_duration_minutes: int
    route_geometry: Optional[List[tuple]] = None  # List of (lat, lon) points


# ============== WebSocket Schemas ==============
class WebSocketMessage(BaseModel):
    type: str  # "sensor_update", "alert", "bin_update"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)


# ============== Filter/Query Schemas ==============
class BinFilter(BaseModel):
    bin_type: Optional[BinTypeEnum] = None
    status: Optional[BinStatusEnum] = None
    min_fill_level: Optional[float] = Field(None, ge=0, le=100)
    max_fill_level: Optional[float] = Field(None, ge=0, le=100)


class AlertFilter(BaseModel):
    alert_type: Optional[AlertTypeEnum] = None
    severity: Optional[AlertSeverityEnum] = None
    is_resolved: Optional[bool] = None
    bin_id: Optional[int] = None
