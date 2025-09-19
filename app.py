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
import sys
from translations import t

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

        # Test connection and check if tables exist
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bus_status'")
            table_exists = cursor.fetchone()[0] > 0
            if not table_exists:
                logger.warning("Database tables not found. Initializing database...")
                try:
                    # Initialize database directly
                    from bus_monitor_pg import BusMonitor
                    monitor = BusMonitor(database_url)
                    logger.info("Database schema created successfully")

                    # Try to download GTFS data
                    logger.info("Attempting to download GTFS data...")
                    if monitor.download_and_update_gtfs():
                        logger.info("GTFS data loaded successfully")
                    else:
                        logger.warning("GTFS data download failed, but schema is ready")

                except Exception as init_error:
                    logger.error(f"Database initialization failed: {init_error}")
                    logger.error("Web app will start but may have limited functionality")

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
        finally:
            if conn:
                db_pool.putconn(conn)

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

@app.route('/health')
def health_check():
    """Health check endpoint for Railway."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return_db_connection(conn)
        return "OK", 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return "Database connection failed", 503


@app.route('/db-status')
def database_status():
    """Show database status for debugging."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        status_info = {}

        # Check each table
        tables = ['bus_status', 'gtfs_stops', 'gtfs_routes', 'gtfs_versions', 'bus_delays']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status_info[table] = f"✅ {count} records"
            except psycopg2.errors.UndefinedTable:
                status_info[table] = "❌ Table does not exist"
            except Exception as e:
                status_info[table] = f"⚠️ Error: {str(e)}"

        # Check for active GTFS version
        try:
            cursor.execute("SELECT COUNT(*) FROM gtfs_versions WHERE is_active = TRUE")
            active_gtfs = cursor.fetchone()[0]
            status_info['active_gtfs'] = f"✅ {active_gtfs} active GTFS version(s)" if active_gtfs > 0 else "❌ No active GTFS version"
        except:
            status_info['active_gtfs'] = "❌ Cannot check GTFS versions"

        return_db_connection(conn)

        # Format as HTML
        html = "<h1>Database Status</h1><ul>"
        for key, value in status_info.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        html += '<p><a href="/monitor-status">Monitor Status</a> | <a href="/debug-data">Debug Data</a> | <a href="/batch-timing">Batch Timing</a> | <a href="/stop-analysis">Stop Analysis</a> | <a href="/linking-debug">Linking Debug</a> | <a href="/">Home</a></p>'

        return html, 200

    except Exception as e:
        return f"Database connection failed: {str(e)}", 500


@app.route('/debug-data')
def debug_data():
    """Debug data types in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check recent bus_status records
        cursor.execute("""
            SELECT id, latitude, longitude, heading, speed_kmh, linked_id, recorded_at
            FROM bus_status
            ORDER BY recorded_at DESC
            LIMIT 5
        """)

        records = cursor.fetchall()
        return_db_connection(conn)

        html = "<h1>Data Type Debug</h1><h2>Recent Bus Status Records:</h2><ul>"

        for record in records:
            html += f"<li><strong>ID {record['id']}:</strong><br>"
            for key, value in record.items():
                html += f"&nbsp;&nbsp;{key}: {value} (type: {type(value).__name__})<br>"
            html += "</li><br>"

        html += "</ul>"
        html += f"<p>Total records found: {len(records)}</p>"
        html += '<p><a href="/db-status">Database Status</a> | <a href="/">Home</a></p>'

        return html, 200

    except Exception as e:
        logger.error(f"Debug data failed: {e}")
        import traceback
        traceback.print_exc()
        return f"Debug failed: {str(e)}", 500


@app.route('/batch-timing')
def batch_timing():
    """Check timing between recent data batches."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get last 10 batch timestamps
        cursor.execute("""
            SELECT DISTINCT recorded_at,
                   COUNT(*) as record_count,
                   COUNT(*) FILTER (WHERE speed_kmh IS NOT NULL) as with_speed,
                   COUNT(*) FILTER (WHERE linked_id IS NOT NULL) as with_links
            FROM bus_status
            GROUP BY recorded_at
            ORDER BY recorded_at DESC
            LIMIT 10
        """)

        batches = cursor.fetchall()
        return_db_connection(conn)

        html = "<h1>Batch Timing Analysis</h1><table border='1'>"
        html += "<tr><th>Recorded At</th><th>Records</th><th>With Speed</th><th>With Links</th><th>Gap (seconds)</th></tr>"

        prev_time = None
        for i, batch in enumerate(batches):
            recorded_at = batch['recorded_at']
            gap = ""
            if prev_time:
                gap_seconds = (prev_time - recorded_at).total_seconds()
                gap = f"{gap_seconds:.1f}s"

            html += f"""
                <tr>
                    <td>{recorded_at}</td>
                    <td>{batch['record_count']}</td>
                    <td>{batch['with_speed']}</td>
                    <td>{batch['with_links']}</td>
                    <td>{gap}</td>
                </tr>
            """
            prev_time = recorded_at

        html += "</table>"
        html += '<p><a href="/db-status">Database Status</a> | <a href="/">Home</a></p>'

        return html, 200

    except Exception as e:
        logger.error(f"Batch timing check failed: {e}")
        return f"Batch timing check failed: {str(e)}", 500

@app.route('/stop-analysis')
def stop_analysis():
    """Analyze stop data in recent bus records."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get recent records with stop information
        cursor.execute("""
            SELECT route, stop_id, next_stop_id, recorded_at,
                   COUNT(*) as count
            FROM bus_status
            WHERE recorded_at >= NOW() - INTERVAL '1 hour'
            GROUP BY route, stop_id, next_stop_id, recorded_at
            ORDER BY recorded_at DESC, route, stop_id
            LIMIT 50
        """)

        records = cursor.fetchall()

        # Get overall stop statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_records,
                COUNT(*) FILTER (WHERE stop_id IS NOT NULL) as with_stop_id,
                COUNT(*) FILTER (WHERE next_stop_id IS NOT NULL) as with_next_stop_id,
                COUNT(DISTINCT stop_id) FILTER (WHERE stop_id IS NOT NULL) as unique_stops,
                COUNT(DISTINCT next_stop_id) FILTER (WHERE next_stop_id IS NOT NULL) as unique_next_stops
            FROM bus_status
            WHERE recorded_at >= NOW() - INTERVAL '1 hour'
        """)

        stats = cursor.fetchone()

        # Check for recent stop changes in linked records
        cursor.execute("""
            SELECT
                curr.route,
                prev.stop_id as prev_stop,
                curr.stop_id as curr_stop,
                curr.recorded_at
            FROM bus_status curr
            JOIN bus_status prev ON curr.linked_id = prev.id
            WHERE curr.recorded_at >= NOW() - INTERVAL '30 minutes'
            AND curr.stop_id IS NOT NULL
            AND prev.stop_id IS NOT NULL
            AND curr.stop_id != prev.stop_id
            ORDER BY curr.recorded_at DESC
            LIMIT 10
        """)

        recent_changes = cursor.fetchall()

        return_db_connection(conn)

        html = "<h1>Stop Data Analysis</h1>"

        html += "<h2>Overall Statistics (Last Hour)</h2><ul>"
        html += f"<li>Total records: {stats['total_records']}</li>"
        html += f"<li>With stop_id: {stats['with_stop_id']}</li>"
        html += f"<li>With next_stop_id: {stats['with_next_stop_id']}</li>"
        html += f"<li>Unique stops: {stats['unique_stops']}</li>"
        html += f"<li>Unique next stops: {stats['unique_next_stops']}</li>"
        html += "</ul>"

        html += f"<h2>Recent Stop Changes ({len(recent_changes)} found)</h2>"
        if recent_changes:
            html += "<table border='1'><tr><th>Route</th><th>Previous Stop</th><th>Current Stop</th><th>Time</th></tr>"
            for change in recent_changes:
                html += f"<tr><td>{change['route']}</td><td>{change['prev_stop']}</td><td>{change['curr_stop']}</td><td>{change['recorded_at']}</td></tr>"
            html += "</table>"
        else:
            html += "<p>No stop changes detected in linked records (last 30 minutes)</p>"

        html += "<h2>Recent Records Sample</h2>"
        html += "<table border='1'><tr><th>Route</th><th>Stop ID</th><th>Next Stop ID</th><th>Time</th><th>Count</th></tr>"

        for record in records[:20]:  # Show first 20
            html += f"""
                <tr>
                    <td>{record['route']}</td>
                    <td>{record['stop_id'] or 'NULL'}</td>
                    <td>{record['next_stop_id'] or 'NULL'}</td>
                    <td>{record['recorded_at']}</td>
                    <td>{record['count']}</td>
                </tr>
            """

        html += "</table>"
        html += '<p><a href="/db-status">Database Status</a> | <a href="/">Home</a></p>'

        return html, 200

    except Exception as e:
        logger.error(f"Stop analysis failed: {e}")
        return f"Stop analysis failed: {str(e)}", 500

@app.route('/linking-debug')
def linking_debug():
    """Debug the bus linking process."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Overall linking statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_records,
                COUNT(*) FILTER (WHERE linked_id IS NOT NULL) as linked_records,
                COUNT(*) FILTER (WHERE speed_kmh IS NOT NULL) as with_speed,
                COUNT(DISTINCT recorded_at) as unique_batches,
                MAX(recorded_at) as latest_batch,
                MIN(recorded_at) as earliest_batch
            FROM bus_status
        """)

        stats = cursor.fetchone()

        # Recent batch analysis
        cursor.execute("""
            SELECT
                recorded_at,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE linked_id IS NOT NULL) as linked,
                COUNT(*) FILTER (WHERE speed_kmh IS NOT NULL) as with_speed,
                AVG(speed_kmh) FILTER (WHERE speed_kmh IS NOT NULL) as avg_speed
            FROM bus_status
            GROUP BY recorded_at
            ORDER BY recorded_at DESC
            LIMIT 5
        """)

        recent_batches = cursor.fetchall()

        # Sample of recent records
        cursor.execute("""
            SELECT id, route, linked_id, speed_kmh, recorded_at
            FROM bus_status
            WHERE recorded_at >= (SELECT MAX(recorded_at) FROM bus_status)
            LIMIT 10
        """)

        sample_records = cursor.fetchall()

        return_db_connection(conn)

        html = "<h1>Bus Linking Debug</h1>"

        html += "<h2>Overall Statistics</h2><ul>"
        html += f"<li>Total records: {stats['total_records']}</li>"
        html += f"<li>Linked records: {stats['linked_records']} ({(stats['linked_records']/stats['total_records']*100) if stats['total_records'] > 0 else 0:.1f}%)</li>"
        html += f"<li>With speed: {stats['with_speed']}</li>"
        html += f"<li>Unique batches: {stats['unique_batches']}</li>"
        html += f"<li>Latest batch: {stats['latest_batch']}</li>"
        html += "</ul>"

        html += "<h2>Recent Batches</h2>"
        html += "<table border='1'><tr><th>Batch Time</th><th>Total</th><th>Linked</th><th>With Speed</th><th>Avg Speed</th></tr>"
        for batch in recent_batches:
            avg_speed = f"{batch['avg_speed']:.1f}" if batch['avg_speed'] else "N/A"
            html += f"<tr><td>{batch['recorded_at']}</td><td>{batch['total']}</td><td>{batch['linked']}</td><td>{batch['with_speed']}</td><td>{avg_speed}</td></tr>"
        html += "</table>"

        html += "<h2>Latest Records Sample</h2>"
        html += "<table border='1'><tr><th>ID</th><th>Route</th><th>Linked ID</th><th>Speed</th><th>Time</th></tr>"
        for record in sample_records:
            speed = f"{record['speed_kmh']:.1f}" if record['speed_kmh'] else "NULL"
            linked = record['linked_id'] or "NULL"
            html += f"<tr><td>{record['id']}</td><td>{record['route']}</td><td>{linked}</td><td>{speed}</td><td>{record['recorded_at']}</td></tr>"
        html += "</table>"

        html += '<p><a href="/db-status">Database Status</a> | <a href="/">Home</a></p>'

        return html, 200

    except Exception as e:
        logger.error(f"Linking debug failed: {e}")
        return f"Linking debug failed: {str(e)}", 500

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

    except psycopg2.errors.UndefinedTable:
        logger.error("Database tables not found. Run database initialization.")
        return jsonify({'error': t('ERROR_DATABASE_NOT_INITIALIZED')}), 503
    except Exception as e:
        logger.error(f"Error searching stations: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
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
        return jsonify({'error': t('ERROR_INVALID_COORDINATES')}), 400

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
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/station/<stop_id>/delays')
def station_delays(stop_id):
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
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/station/<stop_id>')
def station_detail(stop_id):
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
            return t('ERROR_STATION_NOT_FOUND'), 404

        return render_template('station_detail.html', station=dict(station))

    except Exception as e:
        logger.error(f"Error getting station detail: {e}")
        return "Villa í gagnagrunni", 500
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
        return jsonify({'error': t('ERROR_DATABASE')}), 500
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
        return jsonify({'error': t('ERROR_DATABASE')}), 500
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
        """, (recent_time,))
        recent_records = cursor.fetchone()['recent_records']

        cursor.execute("""
            SELECT COUNT(*) as recent_delays
            FROM bus_delays
            WHERE recorded_at >= %s
        """, (recent_time,))
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
            'latest_update': latest_update.isoformat() if latest_update else None
        })

    except psycopg2.errors.UndefinedTable:
        logger.error("Database tables not found. Run database initialization.")
        return jsonify({
            'total_records': 0,
            'unique_routes': 0,
            'total_delays': 0,
            'recent_records': 0,
            'recent_delays': 0,
            'latest_update': None,
            'error': t('ERROR_DATABASE_NOT_INITIALIZED')
        })
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/analytics/station-route-pairs')
def station_route_pairs():
    """Get station-route pairs with most delays/earliest arrivals."""
    hours = min(int(request.args.get('hours', 24)), 168)

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get most delayed station-route pairs
        cursor.execute("""
            SELECT
                d.stop_id,
                d.route_id,
                s.stop_name,
                r.route_short_name,
                COUNT(*) as arrival_count,
                AVG(d.delay_seconds) as avg_delay_seconds,
                MAX(d.delay_seconds) as max_delay_seconds,
                COUNT(CASE WHEN d.delay_seconds > 300 THEN 1 END) as very_late_count
            FROM bus_delays d
            JOIN gtfs_stops s ON d.stop_id = s.stop_id
            JOIN gtfs_versions vs ON s.version_id = vs.id AND vs.is_active = TRUE
            JOIN gtfs_routes r ON d.route_id = r.route_id
            JOIN gtfs_versions vr ON r.version_id = vr.id AND vr.is_active = TRUE
            WHERE d.recorded_at >= %s
            GROUP BY d.stop_id, d.route_id, s.stop_name, r.route_short_name
            HAVING COUNT(*) >= 3
            ORDER BY avg_delay_seconds DESC
            LIMIT 10
        """, (since_time,))

        most_delayed = cursor.fetchall()

        # Get earliest station-route pairs (most ahead of schedule)
        cursor.execute("""
            SELECT
                d.stop_id,
                d.route_id,
                s.stop_name,
                r.route_short_name,
                COUNT(*) as arrival_count,
                AVG(d.delay_seconds) as avg_delay_seconds,
                MIN(d.delay_seconds) as min_delay_seconds,
                COUNT(CASE WHEN d.delay_seconds < -60 THEN 1 END) as very_early_count
            FROM bus_delays d
            JOIN gtfs_stops s ON d.stop_id = s.stop_id
            JOIN gtfs_versions vs ON s.version_id = vs.id AND vs.is_active = TRUE
            JOIN gtfs_routes r ON d.route_id = r.route_id
            JOIN gtfs_versions vr ON r.version_id = vr.id AND vr.is_active = TRUE
            WHERE d.recorded_at >= %s
            GROUP BY d.stop_id, d.route_id, s.stop_name, r.route_short_name
            HAVING COUNT(*) >= 3
            ORDER BY avg_delay_seconds ASC
            LIMIT 10
        """, (since_time,))

        most_early = cursor.fetchall()

        return jsonify({
            'most_delayed': [dict(row) for row in most_delayed],
            'most_early': [dict(row) for row in most_early]
        })

    except Exception as e:
        logger.error(f"Error getting station-route pairs: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/analytics/delay-histogram')
def delay_histogram():
    """Get delay histogram data by routes."""
    hours = min(int(request.args.get('hours', 24)), 168)

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get delay distribution for all routes
        cursor.execute("""
            SELECT
                d.route_id,
                r.route_short_name,
                r.route_long_name,
                COUNT(*) as total_arrivals,
                -- Histogram bins (in seconds): <-120, -120 to -60, -60 to 0, 0 to 60, 60 to 180, 180 to 300, >300
                COUNT(CASE WHEN d.delay_seconds < -120 THEN 1 END) as very_early,
                COUNT(CASE WHEN d.delay_seconds >= -120 AND d.delay_seconds < -60 THEN 1 END) as early,
                COUNT(CASE WHEN d.delay_seconds >= -60 AND d.delay_seconds < 0 THEN 1 END) as slightly_early,
                COUNT(CASE WHEN d.delay_seconds >= 0 AND d.delay_seconds <= 60 THEN 1 END) as on_time,
                COUNT(CASE WHEN d.delay_seconds > 60 AND d.delay_seconds <= 180 THEN 1 END) as slightly_late,
                COUNT(CASE WHEN d.delay_seconds > 180 AND d.delay_seconds <= 300 THEN 1 END) as late,
                COUNT(CASE WHEN d.delay_seconds > 300 THEN 1 END) as very_late,
                AVG(d.delay_seconds) as avg_delay,
                STDDEV(d.delay_seconds) as delay_stddev
            FROM bus_delays d
            JOIN gtfs_routes r ON d.route_id = r.route_id
            JOIN gtfs_versions v ON r.version_id = v.id AND v.is_active = TRUE
            WHERE d.recorded_at >= %s
            GROUP BY d.route_id, r.route_short_name, r.route_long_name
            HAVING COUNT(*) >= 5
            ORDER BY total_arrivals DESC
        """, (since_time,))

        histogram_data = cursor.fetchall()

        return jsonify([dict(row) for row in histogram_data])

    except Exception as e:
        logger.error(f"Error getting delay histogram: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/monitor-status')
def monitor_status():
    """Show background monitor status."""
    from background_monitor import background_monitor
    status = background_monitor.get_status()

    html = f"""
    <h1>Background Monitor Status</h1>
    <ul>
        <li><strong>Running:</strong> {'✅ Yes' if status['running'] else '❌ No'}</li>
        <li><strong>Interval:</strong> {status['interval']} seconds</li>
        <li><strong>Database:</strong> {'✅ Configured' if status['database_configured'] else '❌ Not configured'}</li>
    </ul>
    <p>
        <a href="/db-status">Database Status</a> |
        <a href="/">Home</a>
    </p>
    """
    return html, 200


if __name__ == '__main__':
    init_db_pool()

    # Note: Background monitoring is automatically started by gunicorn.conf.py when running in production
    # This block only runs when testing locally with `python app.py`

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)