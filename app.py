#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
import os
import math
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database connection pool
db_pool = None

def init_db_pool():
    """Initialize database connection pool."""
    global db_pool
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    try:
        db_pool = SimpleConnectionPool(1, 20, database_url)
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise

def get_db_connection():
    """Get a database connection from the pool."""
    if db_pool is None:
        init_db_pool()
    return db_pool.getconn()

def return_db_connection(conn):
    """Return a connection to the pool."""
    if db_pool and conn:
        db_pool.putconn(conn)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in meters."""
    R = 6371000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

@app.route('/')
def index():
    """Main page with station search."""
    return render_template('index.html')

@app.route('/api/stations/search')
def search_stations():
    """API endpoint for station search with autocomplete."""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)

    if len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT DISTINCT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code
            FROM gtfs_stops s
            JOIN gtfs_versions v ON s.version_id = v.id
            WHERE v.is_active = TRUE
            AND (LOWER(s.stop_name) LIKE LOWER(%s) OR LOWER(s.stop_code) LIKE LOWER(%s))
            ORDER BY s.stop_name
            LIMIT %s
        """, (f'%{query}%', f'%{query}%', limit))

        stations = cursor.fetchall()
        return jsonify([dict(station) for station in stations])

    except Exception as e:
        logger.error(f"Error searching stations: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/stations/nearby')
def nearby_stations():
    """Find stations near a given coordinate."""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = min(float(request.args.get('radius', 1000)), 5000)  # Max 5km
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Use Haversine formula in SQL (approximate)
        cursor.execute("""
            SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code,
                   6371000 * acos(
                       cos(radians(%s)) * cos(radians(s.stop_lat)) *
                       cos(radians(s.stop_lon) - radians(%s)) +
                       sin(radians(%s)) * sin(radians(s.stop_lat))
                   ) AS distance
            FROM gtfs_stops s
            JOIN gtfs_versions v ON s.version_id = v.id
            WHERE v.is_active = TRUE
            AND s.stop_lat IS NOT NULL AND s.stop_lon IS NOT NULL
            HAVING distance <= %s
            ORDER BY distance
            LIMIT 20
        """, (lat, lon, lat, radius))

        stations = cursor.fetchall()
        return jsonify([dict(station) for station in stations])

    except Exception as e:
        logger.error(f"Error finding nearby stations: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/station/<stop_id>/delays')
def station_delays():
    """Get latest delay information for a specific station."""
    hours = min(int(request.args.get('hours', 24)), 168)  # Max 7 days

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get recent delays for this station
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        cursor.execute("""
            SELECT
                d.route_id,
                d.scheduled_arrival_time,
                d.actual_arrival_time,
                d.delay_seconds,
                r.route_short_name,
                r.route_long_name,
                s.stop_name
            FROM bus_delays d
            JOIN gtfs_routes r ON d.route_id = r.route_id
            JOIN gtfs_versions v1 ON r.version_id = v1.id AND v1.is_active = TRUE
            JOIN gtfs_stops s ON d.stop_id = s.stop_id
            JOIN gtfs_versions v2 ON s.version_id = v2.id AND v2.is_active = TRUE
            WHERE d.stop_id = %s
            AND d.recorded_at >= %s
            ORDER BY d.actual_arrival_time DESC
            LIMIT 100
        """, (stop_id, since_time.isoformat()))

        delays = cursor.fetchall()

        # Get delay statistics
        cursor.execute("""
            SELECT
                d.route_id,
                r.route_short_name,
                COUNT(*) as total_arrivals,
                AVG(d.delay_seconds) as avg_delay,
                MIN(d.delay_seconds) as min_delay,
                MAX(d.delay_seconds) as max_delay,
                COUNT(CASE WHEN d.delay_seconds > 60 THEN 1 END) as late_arrivals,
                COUNT(CASE WHEN d.delay_seconds < -60 THEN 1 END) as early_arrivals
            FROM bus_delays d
            JOIN gtfs_routes r ON d.route_id = r.route_id
            JOIN gtfs_versions v ON r.version_id = v.id AND v.is_active = TRUE
            WHERE d.stop_id = %s
            AND d.recorded_at >= %s
            GROUP BY d.route_id, r.route_short_name
            ORDER BY total_arrivals DESC
        """, (stop_id, since_time.isoformat()))

        stats = cursor.fetchall()

        return jsonify({
            'delays': [dict(delay) for delay in delays],
            'stats': [dict(stat) for stat in stats]
        })

    except Exception as e:
        logger.error(f"Error getting station delays: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/station/<stop_id>')
def station_detail():
    """Station detail page."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code
            FROM gtfs_stops s
            JOIN gtfs_versions v ON s.version_id = v.id
            WHERE v.is_active = TRUE AND s.stop_id = %s
        """, (stop_id,))

        station = cursor.fetchone()
        if not station:
            return "Station not found", 404

        return render_template('station_detail.html', station=dict(station))

    except Exception as e:
        logger.error(f"Error getting station detail: {e}")
        return "Database error", 500
    finally:
        return_db_connection(conn)

@app.route('/analytics')
def analytics():
    """Analytics dashboard."""
    return render_template('analytics.html')

@app.route('/api/analytics/speed-data')
def speed_data():
    """Get speed data for heatmap."""
    hours = min(int(request.args.get('hours', 24)), 168)  # Max 7 days

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        cursor.execute("""
            SELECT
                latitude, longitude, speed_kmh, route
            FROM bus_status
            WHERE speed_kmh IS NOT NULL
            AND speed_kmh > 0
            AND speed_kmh < 100  -- Filter out unrealistic speeds
            AND recorded_at >= %s
            ORDER BY recorded_at DESC
            LIMIT 5000
        """, (since_time.isoformat(),))

        speeds = cursor.fetchall()
        return jsonify([dict(speed) for speed in speeds])

    except Exception as e:
        logger.error(f"Error getting speed data: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/analytics/route-stats')
def route_stats():
    """Get route delay statistics."""
    hours = min(int(request.args.get('hours', 24)), 168)

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        cursor.execute("""
            SELECT
                d.route_id,
                r.route_short_name,
                r.route_long_name,
                COUNT(*) as total_arrivals,
                AVG(d.delay_seconds) as avg_delay,
                STDDEV(d.delay_seconds) as delay_stddev,
                MIN(d.delay_seconds) as min_delay,
                MAX(d.delay_seconds) as max_delay,
                COUNT(CASE WHEN d.delay_seconds > 300 THEN 1 END) as very_late,
                COUNT(CASE WHEN d.delay_seconds BETWEEN 61 AND 300 THEN 1 END) as late,
                COUNT(CASE WHEN d.delay_seconds BETWEEN -60 AND 60 THEN 1 END) as on_time,
                COUNT(CASE WHEN d.delay_seconds < -60 THEN 1 END) as early
            FROM bus_delays d
            JOIN gtfs_routes r ON d.route_id = r.route_id
            JOIN gtfs_versions v ON r.version_id = v.id AND v.is_active = TRUE
            WHERE d.recorded_at >= %s
            GROUP BY d.route_id, r.route_short_name, r.route_long_name
            HAVING COUNT(*) >= 5  -- Only routes with significant data
            ORDER BY total_arrivals DESC
        """, (since_time.isoformat(),))

        stats = cursor.fetchall()
        return jsonify([dict(stat) for stat in stats])

    except Exception as e:
        logger.error(f"Error getting route stats: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/analytics/system-stats')
def system_stats():
    """Get overall system statistics."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Basic counts
        cursor.execute("SELECT COUNT(*) as total_records FROM bus_status")
        total_records = cursor.fetchone()['total_records']

        cursor.execute("SELECT COUNT(DISTINCT route) as unique_routes FROM bus_status")
        unique_routes = cursor.fetchone()['unique_routes']

        cursor.execute("SELECT COUNT(*) as total_delays FROM bus_delays")
        total_delays = cursor.fetchone()['total_delays']

        # Recent activity (last 24 hours)
        recent_time = datetime.now(timezone.utc) - timedelta(hours=24)
        cursor.execute("""
            SELECT COUNT(*) as recent_records
            FROM bus_status
            WHERE recorded_at >= %s
        """, (recent_time.isoformat(),))
        recent_records = cursor.fetchone()['recent_records']

        cursor.execute("""
            SELECT COUNT(*) as recent_delays
            FROM bus_delays
            WHERE recorded_at >= %s
        """, (recent_time.isoformat(),))
        recent_delays = cursor.fetchone()['recent_delays']

        # Latest update
        cursor.execute("SELECT MAX(recorded_at) as latest_update FROM bus_status")
        latest_update = cursor.fetchone()['latest_update']

        return jsonify({
            'total_records': total_records,
            'unique_routes': unique_routes,
            'total_delays': total_delays,
            'recent_records': recent_records,
            'recent_delays': recent_delays,
            'latest_update': latest_update
        })

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        return_db_connection(conn)

if __name__ == '__main__':
    init_db_pool()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)