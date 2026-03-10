# Smart Waste Management System

A comprehensive IoT-based waste management platform that monitors bin fill levels in real-time, provides predictive analytics, and optimizes collection routes to improve operational efficiency.

![Smart Waste Management](docs/screenshot.png)

## Features

### Real-Time Monitoring
- Live bin fill level tracking via IoT sensors
- WebSocket-based real-time updates
- Interactive map showing bin locations and status
- Battery level monitoring for sensors

### Analytics & Predictions
- Fill pattern analysis by hour, day, and zone
- Predictive fill level forecasting (24h, 7d)
- Collection efficiency metrics
- Cost savings analysis
- Historical data visualization

### Route Optimization
- Smart route generation based on fill levels
- Nearest-neighbor TSP algorithm for optimization
- Vehicle capacity and time constraints
- Route tracking and completion

### Alert System
- Critical fill level alerts (>95%)
- High fill level warnings (>80%)
- Low battery notifications
- Sensor offline detection
- Alert resolution workflow

### Dashboard
- Comprehensive statistics overview
- Real-time charts and visualizations
- Critical alerts panel
- Priority bins list
- Responsive design

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **SQLAlchemy** ORM with SQLite
- **WebSocket** for real-time updates
- **Pandas/NumPy** for data analytics
- **Scikit-learn** for predictive modeling

### Frontend
- **HTML5/CSS3/JavaScript** (Vanilla)
- **Chart.js** for data visualization
- **Leaflet.js** for interactive maps
- **Font Awesome** for icons

### IoT Simulator
- Python asyncio for sensor simulation
- Realistic waste generation patterns
- Battery drain simulation

## Project Structure

```
smart-waste-management/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database connection
│   │   ├── websocket.py         # WebSocket handler
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── waste_bin.py
│   │   │   ├── sensor_reading.py
│   │   │   ├── alert.py
│   │   │   ├── collection_route.py
│   │   │   └── collection_event.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── bins.py
│   │   │   ├── readings.py
│   │   │   ├── analytics.py
│   │   │   ├── alerts.py
│   │   │   └── routes.py
│   │   ├── services/            # Business logic
│   │   │   ├── analytics_service.py
│   │   │   ├── alert_service.py
│   │   │   └── route_service.py
│   │   └── utils/               # Helper functions
│   │       └── schemas.py       # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Main HTML file
│   ├── css/
│   │   └── styles.css           # Stylesheet
│   └── js/
│       ├── config.js            # Configuration
│       ├── api.js               # API client
│       ├── charts.js            # Chart manager
│       ├── map.js               # Map manager
│       └── app.js               # Main application
├── iot_simulator/
│   ├── simulator.py             # IoT sensor simulator
│   └── requirements.txt
├── docs/
│   ├── api.md                   # API documentation
│   └── deployment.md            # Deployment guide
├── .gitignore
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart-waste-management.git
cd smart-waste-management
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install IoT simulator dependencies (optional):
```bash
cd ../iot_simulator
pip install -r requirements.txt
```

### Running the Application

1. Start the backend server:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Seed the database with sample data:
```bash
curl -X POST http://localhost:8000/api/v1/seed-data
```

3. Open the frontend:
   - Open `frontend/index.html` in your browser, or
   - Access `http://localhost:8000` (backend serves frontend)

4. (Optional) Start the IoT simulator:
```bash
cd iot_simulator
python simulator.py
```

### Access the Application

- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Endpoints**: http://localhost:8000/api/v1/

## API Endpoints

### Waste Bins
- `GET /api/v1/bins` - List all bins
- `GET /api/v1/bins/{id}` - Get bin details
- `POST /api/v1/bins` - Create new bin
- `PUT /api/v1/bins/{id}` - Update bin
- `DELETE /api/v1/bins/{id}` - Delete bin
- `GET /api/v1/bins/{id}/readings` - Get bin sensor history

### Sensor Readings
- `GET /api/v1/readings` - Get all readings
- `POST /api/v1/readings` - Submit new reading
- `GET /api/v1/readings/latest` - Get latest readings

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard stats
- `GET /api/v1/analytics/fill-patterns` - Fill pattern analysis
- `GET /api/v1/analytics/predictions` - Fill predictions
- `GET /api/v1/analytics/efficiency` - Efficiency metrics
- `GET /api/v1/analytics/zones` - Zone analysis

### Alerts
- `GET /api/v1/alerts` - List alerts
- `POST /api/v1/alerts/{id}/resolve` - Resolve alert
- `GET /api/v1/alerts/unresolved` - Get unresolved alerts

### Routes
- `GET /api/v1/routes` - List routes
- `POST /api/v1/routes/optimize` - Optimize route
- `POST /api/v1/routes/generate-smart` - Generate smart route

### WebSocket
- `WS /ws` - Real-time updates

## Configuration

Environment variables (create `.env` file in backend directory):

```env
DEBUG=true
DATABASE_URL=sqlite:///./waste_management.db
SIMULATOR_ENABLED=true
SIMULATOR_UPDATE_INTERVAL=30
ALERT_FILL_THRESHOLD_HIGH=80
ALERT_FILL_THRESHOLD_CRITICAL=95
ALERT_BATTERY_THRESHOLD=20
```

## IoT Simulator

The IoT simulator mimics real sensor behavior with:
- Different waste generation patterns (residential, commercial, recreational)
- Time-based fill rate variations
- Battery drain simulation
- Occasional sensor failures

Run with options:
```bash
python simulator.py --api-url http://localhost:8000 --interval 30 --bins 20
```

## Screenshots

### Dashboard
![Dashboard](docs/dashboard.png)

### Bin Management
![Bins](docs/bins.png)

### Analytics
![Analytics](docs/analytics.png)

### Live Map
![Map](docs/map.png)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FastAPI for the excellent web framework
- Chart.js for beautiful visualizations
- Leaflet.js for interactive maps
- OpenStreetMap for map tiles

## Contact

For questions or support, please open an issue on GitHub.

---

**Made with for a cleaner, smarter future**
