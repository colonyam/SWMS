# API Documentation

## Smart Waste Management System API

Base URL: `http://localhost:8000/api/v1`

---

## Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header for protected endpoints.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1440,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@smartwaste.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true
  }
}
```

### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer <access_token>
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

### Change Password
```http
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

### Logout
Simply discard the tokens on the client side. The tokens will expire automatically.

### Default Credentials
- **Username:** `admin`
- **Password:** `admin123`
- **Important:** Change the default password after first login!

---

## Endpoints

### Dashboard & Analytics

#### Get Dashboard Statistics
```http
GET /analytics/dashboard
```

Returns comprehensive dashboard statistics.

**Response:**
```json
{
  "total_bins": 15,
  "active_bins": 14,
  "maintenance_bins": 1,
  "critical_bins": 2,
  "high_fill_bins": 5,
  "avg_fill_level": 67.5,
  "total_collections_today": 8,
  "unresolved_alerts": 3,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### Get Fill Patterns
```http
GET /analytics/fill-patterns?bin_id=1&days=7
```

Analyzes fill patterns for bins.

**Parameters:**
- `bin_id` (optional): Specific bin ID
- `days`: Number of days to analyze (1-30)

**Response:**
```json
[
  {
    "bin_id": 1,
    "bin_location": "Downtown Main St",
    "hourly_avg": [25.5, 26.1, 27.3, ...],
    "daily_avg": [45.2, 48.1, 52.3, ...],
    "trend": "increasing"
  }
]
```

#### Get Predictions
```http
GET /analytics/predictions?bin_id=1
```

Get fill level predictions for bins.

**Response:**
```json
[
  {
    "bin_id": 1,
    "bin_location": "Downtown Main St",
    "current_fill": 75.5,
    "predicted_fill_24h": 89.2,
    "predicted_fill_7d": 98.5,
    "recommended_collection_time": "2024-01-16T14:30:00",
    "confidence_score": 0.85
  }
]
```

---

### Waste Bins

#### List All Bins
```http
GET /bins?bin_type=general&status=active&include_latest=true
```

**Parameters:**
- `bin_type` (optional): Filter by type (general, recycling, organic, hazardous)
- `status` (optional): Filter by status (active, maintenance, inactive)
- `include_latest` (optional): Include latest sensor reading
- `skip`: Pagination offset
- `limit`: Number of results (max 1000)

**Response:**
```json
[
  {
    "id": 1,
    "location_name": "Downtown Main St",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "bin_type": "general",
    "capacity_liters": 240,
    "status": "active",
    "install_date": "2024-01-01T00:00:00",
    "latest_reading": {
      "fill_level_percent": 75.5,
      "temperature_celsius": 22.5,
      "battery_percent": 89.0,
      "timestamp": "2024-01-15T10:00:00"
    }
  }
]
```

#### Get Bin Details
```http
GET /bins/{bin_id}?include_history=true
```

**Response:**
```json
{
  "id": 1,
  "location_name": "Downtown Main St",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "bin_type": "general",
  "capacity_liters": 240,
  "status": "active",
  "recent_readings": [...]
}
```

#### Create New Bin
```http
POST /bins
Content-Type: application/json

{
  "location_name": "New Location",
  "latitude": 40.7500,
  "longitude": -74.0000,
  "bin_type": "general",
  "capacity_liters": 240
}
```

#### Update Bin
```http
PUT /bins/{bin_id}
Content-Type: application/json

{
  "location_name": "Updated Location",
  "status": "maintenance"
}
```

#### Delete Bin
```http
DELETE /bins/{bin_id}
```

#### Mark Bin as Collected
```http
POST /bins/{bin_id}/collect
Content-Type: application/json

{
  "notes": "Manual collection"
}
```

---

### Sensor Readings

#### Get All Readings
```http
GET /readings?bin_id=1&hours=24
```

**Parameters:**
- `bin_id` (optional): Filter by bin
- `hours` (optional): Time range (1-168)
- `skip`: Pagination offset
- `limit`: Number of results

#### Get Latest Readings
```http
GET /readings/latest
```

Returns the most recent reading for each bin.

#### Submit New Reading
```http
POST /readings
Content-Type: application/json

{
  "bin_id": 1,
  "fill_level_percent": 75.5,
  "temperature_celsius": 22.5,
  "battery_percent": 89.0,
  "timestamp": "2024-01-15T10:00:00"
}
```

#### Submit Batch Readings
```http
POST /readings/batch
Content-Type: application/json

[
  {
    "bin_id": 1,
    "fill_level_percent": 75.5,
    "temperature_celsius": 22.5,
    "battery_percent": 89.0
  },
  {
    "bin_id": 2,
    "fill_level_percent": 60.0,
    "temperature_celsius": 21.0,
    "battery_percent": 95.0
  }
]
```

---

### Alerts

#### List Alerts
```http
GET /alerts?alert_type=fill_level_high&severity=high&is_resolved=false
```

**Parameters:**
- `alert_type` (optional): Filter by type
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `is_resolved` (optional): Filter by status
- `bin_id` (optional): Filter by bin

**Response:**
```json
[
  {
    "id": 1,
    "bin_id": 5,
    "bin_location": "Times Square",
    "alert_type": "fill_level_critical",
    "severity": "critical",
    "message": "Bin is critically full (97.5%). Immediate collection required.",
    "is_resolved": false,
    "created_at": "2024-01-15T09:30:00",
    "resolved_at": null,
    "resolved_by": null,
    "resolution_notes": null
  }
]
```

#### Get Unresolved Alerts
```http
GET /alerts/unresolved?severity=critical
```

#### Resolve Alert
```http
POST /alerts/{alert_id}/resolve
Content-Type: application/json

{
  "resolved_by": "John Doe",
  "resolution_notes": "Collected and emptied"
}
```

#### Get Alert Statistics
```http
GET /alerts/stats/summary?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "total_alerts": 45,
  "by_type": {
    "fill_level_high": 20,
    "fill_level_critical": 10,
    "low_battery": 15
  },
  "by_severity": {
    "low": 15,
    "medium": 15,
    "high": 10,
    "critical": 5
  },
  "unresolved_critical": 2,
  "unresolved_high": 3,
  "avg_resolution_hours": 4.5
}
```

#### Check Offline Sensors
```http
GET /alerts/check/offline-sensors?threshold_minutes=120
```

---

### Collection Routes

#### List Routes
```http
GET /routes?status=planned
```

**Parameters:**
- `status` (optional): Filter by status

**Response:**
```json
[
  {
    "id": 1,
    "route_name": "Downtown Morning Route",
    "vehicle_id": "TRUCK-001",
    "driver_name": "John Doe",
    "scheduled_date": "2024-01-15T08:00:00",
    "estimated_duration_minutes": 180,
    "total_distance_km": 15.5,
    "status": "planned",
    "waypoints": [1, 2, 3, 4, 5],
    "notes": "Priority route for downtown area"
  }
]
```

#### Get Route Details
```http
GET /routes/{route_id}
```

#### Get Route Stops
```http
GET /routes/{route_id}/stops
```

**Response:**
```json
{
  "route_id": 1,
  "stop_count": 5,
  "stops": [
    {
      "stop_number": 1,
      "bin_id": 1,
      "location": "Downtown Main St",
      "coordinates": [40.7128, -74.0060],
      "fill_level": 85.5,
      "collected": false,
      "collected_at": null
    }
  ]
}
```

#### Create Route
```http
POST /routes
Content-Type: application/json

{
  "route_name": "New Route",
  "vehicle_id": "TRUCK-002",
  "driver_name": "Jane Smith",
  "scheduled_date": "2024-01-16T08:00:00",
  "waypoints": [1, 2, 3],
  "notes": "Morning collection"
}
```

#### Optimize Route
```http
POST /routes/optimize
Content-Type: application/json

{
  "bin_ids": [1, 2, 3, 4, 5],
  "start_location": [40.7128, -74.0060],
  "vehicle_capacity": 5000
}
```

**Response:**
```json
{
  "optimized_order": [1, 3, 2, 5, 4],
  "waypoint_details": [...],
  "estimated_distance_km": 12.5,
  "estimated_duration_minutes": 150,
  "total_bins": 5,
  "total_volume_liters": 850,
  "route_geometry": [[40.7128, -74.0060], ...]
}
```

#### Generate Smart Route
```http
POST /routes/generate-smart?zone=Downtown&max_bins=15&min_fill_level=60
```

Automatically generates an optimized route based on current bin statuses.

#### Start Route
```http
POST /routes/{route_id}/start
```

#### Complete Route
```http
POST /routes/{route_id}/complete
```

---

## WebSocket

### Connection
```
WS /ws
```

### Message Types

#### Sensor Update
```json
{
  "type": "sensor_update",
  "data": {
    "bin_id": 1,
    "fill_level_percent": 75.5,
    "timestamp": "2024-01-15T10:00:00"
  },
  "timestamp": "2024-01-15T10:00:00"
}
```

#### Alert
```json
{
  "type": "alert",
  "data": {
    "alert_id": 1,
    "bin_id": 5,
    "severity": "critical",
    "message": "Bin is critically full"
  },
  "timestamp": "2024-01-15T10:00:00"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Rate Limiting

For production use, implement rate limiting:
- 100 requests per minute per IP
- 1000 requests per hour per API key

---

## Data Models

### Bin Types
- `general` - General waste
- `recycling` - Recyclable materials
- `organic` - Organic/compostable waste
- `hazardous` - Hazardous materials

### Bin Status
- `active` - Normal operation
- `maintenance` - Under maintenance
- `inactive` - Temporarily inactive

### Alert Types
- `fill_level_high` - Fill level >= 80%
- `fill_level_critical` - Fill level >= 95%
- `low_battery` - Battery <= 20%
- `sensor_offline` - No reading for 2+ hours
- `maintenance_required` - Scheduled maintenance

### Alert Severity
- `low` - Informational
- `medium` - Attention needed
- `high` - Urgent action required
- `critical` - Immediate action required

### Route Status
- `planned` - Scheduled but not started
- `in_progress` - Currently being executed
- `completed` - Successfully finished
- `cancelled` - Cancelled before completion
