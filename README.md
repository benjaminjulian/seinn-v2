# Straeto Bus Monitor

A real-time bus monitoring system for Reykjavik's Straeto bus network with delay tracking, route analysis, and performance analytics.

## Features

- **Real-time Bus Tracking**: Monitors bus positions and calculates speeds between stops
- **Delay Analysis**: Tracks actual vs scheduled arrival times using GTFS data
- **Station Search**: Find stations by name or location with autocomplete
- **Interactive Analytics**: Speed heatmaps, route performance statistics, and delay visualizations
- **Web Interface**: Responsive web app for browsing station delays and system analytics

## Deployment on Railway

### Prerequisites

1. Railway account ([railway.app](https://railway.app))
2. PostgreSQL database service

### Quick Deploy

1. **Create a new Railway project** and connect your GitHub repository

2. **Add PostgreSQL database**:
   - In your Railway project dashboard
   - Click "New Service" → "Database" → "PostgreSQL"
   - Note the database connection details

3. **Set Environment Variables**:
   - `DATABASE_URL`: Your PostgreSQL connection string (automatically set by Railway)
   - `PORT`: Will be set automatically by Railway

4. **Deploy**:
   - Railway will automatically detect the `Procfile` and deploy both services
   - The web service will be available at your Railway-provided URL
   - The worker service will run in the background collecting bus data

### Manual Setup

If you prefer manual deployment:

```bash
# Clone the repository
git clone <your-repo-url>
cd seinn-v2

# Install dependencies locally for testing
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@host:port/database"

# Initialize database (run once)
python bus_monitor_pg.py --force-gtfs

# Test the monitoring script
python bus_monitor_pg.py --once

# Test the web application
python app.py
```

### Services

The deployment includes two services:

1. **Web Service** (`web: gunicorn app:app`):
   - Flask web application
   - Station search and delay information
   - Analytics dashboard with visualizations

2. **Worker Service** (`worker: python bus_monitor_pg.py`):
   - Background bus data collection
   - GTFS data updates
   - Speed calculation and delay tracking

## API Endpoints

- `GET /api/stations/search?q=<query>` - Search stations by name
- `GET /api/stations/nearby?lat=<lat>&lon=<lon>&radius=<meters>` - Find nearby stations
- `GET /api/station/<stop_id>/delays?hours=<hours>` - Get delay data for a station
- `GET /api/analytics/speed-data?hours=<hours>` - Get speed data for heatmap
- `GET /api/analytics/route-stats?hours=<hours>` - Get route performance statistics
- `GET /api/analytics/system-stats` - Get overall system statistics

## Data Sources

- **Bus Locations**: Straeto real-time API (`https://opendata.straeto.is/bus/x8061285850508698/status.xml`)
- **GTFS Data**: Straeto GTFS feed (`https://opendata.straeto.is/data/gtfs/gtfs.zip`)

## Database Schema

### Core Tables

- `bus_status`: Real-time bus positions with calculated speeds
- `bus_delays`: Calculated delays based on GTFS schedules
- `gtfs_*`: GTFS static data (stops, routes, trips, stop_times, calendar)

### Key Features

- Speed calculation using GPS coordinates and timestamps
- Bus linking between consecutive data points
- Delay calculation by comparing actual vs scheduled arrival times
- Automatic GTFS data updates (daily)

## Development

### Local Development

```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DATABASE_URL="postgresql://localhost:5432/bus_monitor"

# Run database setup
python bus_monitor_pg.py --force-gtfs

# Start web server
flask run --debug

# In another terminal, start bus monitoring
python bus_monitor_pg.py
```

### Project Structure

```
├── app.py                 # Flask web application
├── bus_monitor_pg.py      # PostgreSQL bus monitoring script
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment configuration
├── railway.json          # Railway service configuration
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── station_detail.html
│   └── analytics.html
└── static/               # CSS and JavaScript files
    ├── css/main.css
    └── js/
        ├── station-search.js
        ├── station-detail.js
        └── analytics.js
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
- `PORT`: Web server port (optional, defaults to 5000)

### Bus Monitor Settings

- **Polling Interval**: 15 seconds (configurable in `bus_monitor_pg.py`)
- **Speed Gate**: 120 km/h maximum realistic speed for linking buses
- **GTFS Update**: Daily automatic updates

## Monitoring and Maintenance

### Health Checks

- Web service: `GET /` returns the main page
- Database connectivity is tested on each request
- System statistics available at `/api/analytics/system-stats`

### Logs

- Application logs are available in Railway dashboard
- Monitor for GTFS update failures
- Check for database connection issues

### Performance

- Database connection pooling for web requests
- Efficient spatial queries for nearby station search
- Indexed database tables for fast lookups

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]