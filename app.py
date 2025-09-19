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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip loading .env file
    pass

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

        # Test database connection
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            logger.info("Database connection test successful")
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

@app.route('/api/stations/search')
def search_stations():
    """API endpoint for station search with autocomplete.

    Enhanced to return individual stop_ids to handle same-name stops
    in opposite directions, as recommended in the review.
    """
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)
    prefer_stop_code = request.args.get('prefer_stop_code', 'false').lower() == 'true'

    if len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if prefer_stop_code:
            # Search by stop code first (more reliable as noted in review)
            cursor.execute("""
                SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code,
                       'stop_code' as match_type
                FROM gtfs_stops s
                JOIN gtfs_versions v ON s.version_id = v.id
                WHERE v.is_active = TRUE
                AND s.stop_code = %s
                ORDER BY s.stop_name
                LIMIT %s
            """, (query, limit))

            results = cursor.fetchall()

            # If no exact stop code match, fall back to name search
            if not results:
                cursor.execute("""
                    SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code,
                           'stop_name' as match_type
                    FROM gtfs_stops s
                    JOIN gtfs_versions v ON s.version_id = v.id
                    WHERE v.is_active = TRUE
                    AND LOWER(s.stop_name) LIKE LOWER(%s)
                    ORDER BY s.stop_name, s.stop_id
                    LIMIT %s
                """, (f'%{query}%', limit))
                results = cursor.fetchall()
        else:
            # Regular name-based search returning unique station names only
            cursor.execute("""
                SELECT DISTINCT s.stop_name,
                       'stop_name' as match_type
                FROM gtfs_stops s
                JOIN gtfs_versions v ON s.version_id = v.id
                WHERE v.is_active = TRUE
                AND LOWER(s.stop_name) LIKE LOWER(%s)
                ORDER BY s.stop_name
                LIMIT %s
            """, (f'%{query}%', limit))
            results = cursor.fetchall()

        return jsonify([dict(station) for station in results])

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
            SELECT stop_id, stop_name, stop_lat, stop_lon, stop_code, distance
            FROM (
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
            ) AS stations_with_distance
            WHERE distance <= %s
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

@app.route('/station/<stop_name>/buses')
def station_by_name(stop_name):
    """Station detail page by name (redirects to first matching stop_id)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code
            FROM gtfs_stops s
            JOIN gtfs_versions v ON s.version_id = v.id
            WHERE v.is_active = TRUE AND LOWER(s.stop_name) = LOWER(%s)
            ORDER BY s.stop_id
            LIMIT 1
        """, (stop_name,))

        station = cursor.fetchone()
        if not station:
            return t('ERROR_STATION_NOT_FOUND'), 404

        return render_template('station_detail.html', station=dict(station))

    except Exception as e:
        logger.error(f"Error getting station detail: {e}")
        return "Villa í gagnagrunni", 500
    finally:
        return_db_connection(conn)

def get_gtfs_service_date_for_time(current_date, gtfs_time_str):
    """
    Get the GTFS service date for a given time, handling 24+ hour format.
    Times 00:00:00 to 05:30:00 are considered part of the previous service day.
    """
    try:
        parts = gtfs_time_str.split(':')
        if len(parts) != 3:
            return current_date

        hour = int(parts[0])
        minute = int(parts[1])

        # Times from 00:00 to 05:30 (and their 24+ hour equivalents) belong to previous day
        if hour >= 24:
            # 24:00+ times are next day times, but still part of current service day
            return current_date
        elif hour < 6 or (hour == 5 and minute <= 30):
            # Early morning times belong to previous service day
            return current_date - timedelta(days=1)
        else:
            return current_date

    except (ValueError, IndexError):
        return current_date

@app.route('/api/station/<stop_id>/trips')
def station_trips(stop_id):
    """Get all trips that pass through a given station ID for a specific date."""
    # Get date parameter, default to today
    date_str = request.args.get('date')
    if date_str:
        try:
            requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        # Use current date in Iceland timezone (UTC offset aware)
        requested_date = datetime.now(timezone.utc).date()

    # For GTFS, we need to consider both the requested date and the next day
    # because early morning times (00:00-05:30) of the next day belong to the current service day
    service_dates = [requested_date, requested_date + timedelta(days=1)]

    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        all_trips = []

        for service_date in service_dates:
            # Get day of week (0=Monday, 6=Sunday) for calendar lookup
            weekday = service_date.weekday()
            day_columns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_column = day_columns[weekday]

            # Format date for GTFS calendar_dates (YYYYMMDD)
            gtfs_date = service_date.strftime('%Y%m%d')

            # Get trips passing through this station with calendar filtering
            cursor.execute(f"""
                WITH calendar_services AS (
                    -- Services active from regular calendar
                    SELECT DISTINCT c.service_id
                    FROM gtfs_calendar c
                    JOIN gtfs_versions v ON c.version_id = v.id
                    WHERE v.is_active = TRUE
                    AND c.{day_column} = 1
                    AND %s >= c.start_date
                    AND (c.end_date = '' OR c.end_date IS NULL OR %s <= c.end_date)
                ),
                added_services AS (
                    -- Services added by calendar_dates (exception_type = 1)
                    SELECT DISTINCT cd.service_id
                    FROM gtfs_calendar_dates cd
                    JOIN gtfs_versions v ON cd.version_id = v.id
                    WHERE v.is_active = TRUE
                    AND cd.date = %s
                    AND cd.exception_type = 1
                ),
                removed_services AS (
                    -- Services excluded by calendar_dates (exception_type = 2)
                    SELECT DISTINCT cd.service_id
                    FROM gtfs_calendar_dates cd
                    JOIN gtfs_versions v ON cd.version_id = v.id
                    WHERE v.is_active = TRUE
                    AND cd.date = %s
                    AND cd.exception_type = 2
                ),
                active_services AS (
                    -- Combine calendar and added services, exclude removed services
                    SELECT service_id FROM calendar_services
                    UNION
                    SELECT service_id FROM added_services
                    EXCEPT
                    SELECT service_id FROM removed_services
                )
                SELECT DISTINCT
                    t.trip_id,
                    t.route_id,
                    t.trip_headsign,
                    t.direction_id,
                    r.route_short_name,
                    r.route_long_name,
                    st.arrival_time,
                    st.departure_time,
                    st.stop_sequence,
                    t.service_id
                FROM gtfs_stop_times st
                JOIN gtfs_trips t ON st.trip_id = t.trip_id AND st.version_id = t.version_id
                JOIN gtfs_routes r ON t.route_id = r.route_id AND t.version_id = r.version_id
                JOIN gtfs_versions v ON st.version_id = v.id
                JOIN active_services asvc ON t.service_id = asvc.service_id
                WHERE v.is_active = TRUE
                AND st.stop_id = %s
                ORDER BY r.route_short_name, st.arrival_time, t.trip_id
            """, (gtfs_date, gtfs_date, gtfs_date, gtfs_date, stop_id))

            trips = cursor.fetchall()

            # Filter trips based on GTFS time logic
            for trip in trips:
                trip_service_date = get_gtfs_service_date_for_time(service_date, trip['arrival_time'])
                if trip_service_date == requested_date:
                    all_trips.append(dict(trip))

        # Remove duplicates and sort
        unique_trips = {}
        for trip in all_trips:
            trip_key = trip['trip_id']
            if trip_key not in unique_trips:
                unique_trips[trip_key] = trip

        sorted_trips = sorted(unique_trips.values(), key=lambda x: (x['route_short_name'] or '', x['arrival_time'], x['trip_id']))

        if not sorted_trips:
            return jsonify({'error': 'Station not found or no trips found for this date'}), 404

        return jsonify({
            'stop_id': stop_id,
            'service_date': requested_date.isoformat(),
            'trips': sorted_trips
        })

    except Exception as e:
        logger.error(f"Error getting station trips: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/station/<stop_id>/approaching-buses')
def station_approaching_buses(stop_id):
    """Get buses currently approaching a given station."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            WITH RECURSIVE
            latest_batch AS (
              SELECT MAX(recorded_at) AS ts FROM bus_status WHERE linked_id IS NOT NULL
            ),
            recent AS (
              SELECT *
              FROM bus_status
              WHERE recorded_at = (SELECT ts FROM latest_batch)
            ),
            latest_per_busish AS (
              SELECT DISTINCT ON (route, next_stop_id, stop_id, latitude, longitude)
                     *
              FROM recent
              ORDER BY route, next_stop_id, stop_id, latitude, longitude, recorded_at DESC
            ),
            routes AS (
              SELECT r.route_id, r.route_short_name, r.route_long_name
              FROM gtfs_routes r
              JOIN gtfs_versions v ON r.version_id = v.id
              WHERE v.is_active = TRUE
            ),
            matched_by_next AS (
              SELECT
                b.id AS bus_id,
                b.route,
                b.latitude, b.longitude, b.heading, b.fix_type,
                b.stop_id, b.next_stop_id, b.code, b.recorded_at,
                r.route_id, r.route_long_name,
                t.trip_id, t.trip_headsign,
                st_next.stop_sequence   AS bus_seq,
                st_target.stop_sequence AS target_seq,
                (st_target.stop_sequence - st_next.stop_sequence) AS stops_away,
                'next'::text AS match_source
              FROM latest_per_busish b
              JOIN routes r           ON r.route_short_name = b.route
              JOIN gtfs_trips t       ON t.route_id = r.route_id
              JOIN gtfs_versions v1   ON t.version_id = v1.id AND v1.is_active = TRUE
              JOIN gtfs_stop_times st_next
                                  ON st_next.trip_id = t.trip_id
                                 AND st_next.version_id = t.version_id
                                 AND st_next.stop_id = b.next_stop_id
              JOIN gtfs_stop_times st_target
                                  ON st_target.trip_id = t.trip_id
                                 AND st_target.version_id = t.version_id
                                 AND st_target.stop_id = %s
              WHERE b.next_stop_id IS NOT NULL
                AND st_target.stop_sequence >= st_next.stop_sequence
            ),
            matched_by_curr AS (
              SELECT
                b.id AS bus_id,
                b.route,
                b.latitude, b.longitude, b.heading, b.fix_type,
                b.stop_id, b.next_stop_id, b.code, b.recorded_at,
                r.route_id, r.route_long_name,
                t.trip_id, t.trip_headsign,
                st_curr.stop_sequence   AS bus_seq,
                st_target.stop_sequence AS target_seq,
                (st_target.stop_sequence - st_curr.stop_sequence) AS stops_away,
                'curr'::text AS match_source
              FROM latest_per_busish b
              JOIN routes r           ON r.route_short_name = b.route
              JOIN gtfs_trips t       ON t.route_id = r.route_id
              JOIN gtfs_versions v1   ON t.version_id = v1.id AND v1.is_active = TRUE
              JOIN gtfs_stop_times st_curr
                                  ON st_curr.trip_id = t.trip_id
                                 AND st_curr.version_id = t.version_id
                                 AND st_curr.stop_id = b.stop_id
              JOIN gtfs_stop_times st_target
                                  ON st_target.trip_id = t.trip_id
                                 AND st_target.version_id = t.version_id
                                 AND st_target.stop_id = %s
              WHERE b.stop_id IS NOT NULL
                AND st_target.stop_sequence >= st_curr.stop_sequence
            ),
            combined AS (
              SELECT * FROM matched_by_next
              UNION ALL
              SELECT * FROM matched_by_curr
            ),
            ranked AS (
              SELECT
                c.*,
                ROW_NUMBER() OVER (
                  PARTITION BY c.bus_id
                  ORDER BY c.stops_away ASC, c.match_source = 'next' DESC
                ) AS rn
              FROM combined c
              WHERE c.stops_away >= 0
            ),
            picked AS (
              SELECT *
              FROM ranked
              WHERE rn = 1
            ),
            chain(bs_id, cur_id, depth) AS (
              SELECT p.bus_id, p.bus_id, 0
              FROM picked p
              UNION ALL
              SELECT c.bs_id, bs.linked_id, c.depth + 1
              FROM chain c
              JOIN bus_status bs ON bs.id = c.cur_id
              WHERE bs.linked_id IS NOT NULL
                AND c.depth < 200
            ),
            delays_join AS (
              SELECT
                c.bs_id,
                c.depth,
                bd.bus_status_id,
                bd.route_id      AS delay_route_id,
                bd.stop_id       AS delay_stop_id,
                bd.scheduled_arrival_time,
                bd.actual_arrival_time,
                bd.delay_seconds,
                bd.recorded_at   AS delay_recorded_at,
                bd.gtfs_version_id
              FROM chain c
              JOIN bus_delays bd ON bd.bus_status_id = c.cur_id
            ),
            latest_delay_per_bus AS (
              SELECT DISTINCT ON (bs_id)
                     *
              FROM delays_join
              ORDER BY bs_id, depth ASC
            )
            SELECT
              p.bus_id               AS id,
              p.route,
              p.latitude, p.longitude, p.heading, p.fix_type,
              p.stop_id, p.next_stop_id, p.code, p.recorded_at,
              p.route_id, p.route_long_name,
              p.trip_id, p.trip_headsign,
              p.bus_seq, p.target_seq,
              p.stops_away,
              p.match_source,
              ld.delay_stop_id,
              ld.scheduled_arrival_time,
              ld.actual_arrival_time,
              ld.delay_seconds,
              ld.delay_recorded_at,
              ld.gtfs_version_id
            FROM picked p
            LEFT JOIN latest_delay_per_bus ld
                   ON ld.bs_id = p.bus_id
                   AND (ld.delay_route_id::text = p.route::text)
            ORDER BY p.route, p.stops_away, p.recorded_at DESC
        """, (stop_id, stop_id))

        buses = cursor.fetchall()

        return jsonify({
            'stop_id': stop_id,
            'approaching_buses': [dict(bus) for bus in buses],
            'count': len(buses)
        })

    except Exception as e:
        logger.error(f"Error getting approaching buses: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/station-name/<station_name>/buses')
def station_name_approaching_buses(station_name):
    """Get approaching buses for all stations with a given name."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # First, get all stations with this name
        cursor.execute("""
            SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.stop_code
            FROM gtfs_stops s
            JOIN gtfs_versions v ON s.version_id = v.id
            WHERE v.is_active = TRUE
            AND LOWER(s.stop_name) = LOWER(%s)
            ORDER BY s.stop_id
        """, (station_name,))

        stations = cursor.fetchall()

        if not stations:
            return jsonify({'error': 'No stations found with this name'}), 404

        # Get approaching buses for each station
        all_buses = []
        for station in stations:
            # Use the existing approaching-buses query for each station
            cursor.execute("""
                WITH RECURSIVE
                latest_batch AS (
                  SELECT MAX(recorded_at) AS ts FROM bus_status WHERE linked_id IS NOT NULL
                ),
                recent AS (
                  SELECT *
                  FROM bus_status
                  WHERE recorded_at = (SELECT ts FROM latest_batch)
                ),
                latest_per_busish AS (
                  SELECT DISTINCT ON (route, next_stop_id, stop_id, latitude, longitude)
                         *
                  FROM recent
                  ORDER BY route, next_stop_id, stop_id, latitude, longitude, recorded_at DESC
                ),
                routes AS (
                  SELECT r.route_id, r.route_short_name, r.route_long_name
                  FROM gtfs_routes r
                  JOIN gtfs_versions v ON r.version_id = v.id
                  WHERE v.is_active = TRUE
                ),
                matched_by_next AS (
                  SELECT
                    b.id AS bus_id,
                    b.route,
                    b.latitude, b.longitude, b.heading, b.fix_type,
                    b.stop_id, b.next_stop_id, b.code, b.recorded_at,
                    r.route_id, r.route_long_name,
                    t.trip_id, t.trip_headsign,
                    st_next.stop_sequence   AS bus_seq,
                    st_target.stop_sequence AS target_seq,
                    (st_target.stop_sequence - st_next.stop_sequence) AS stops_away,
                    'next'::text AS match_source
                  FROM latest_per_busish b
                  JOIN routes r           ON r.route_short_name = b.route
                  JOIN gtfs_trips t       ON t.route_id = r.route_id
                  JOIN gtfs_versions v1   ON t.version_id = v1.id AND v1.is_active = TRUE
                  JOIN gtfs_stop_times st_next
                                      ON st_next.trip_id = t.trip_id
                                     AND st_next.version_id = t.version_id
                                     AND st_next.stop_id = b.next_stop_id
                  JOIN gtfs_stop_times st_target
                                      ON st_target.trip_id = t.trip_id
                                     AND st_target.version_id = t.version_id
                                     AND st_target.stop_id = %s
                  WHERE b.next_stop_id IS NOT NULL
                    AND st_target.stop_sequence >= st_next.stop_sequence
                ),
                matched_by_curr AS (
                  SELECT
                    b.id AS bus_id,
                    b.route,
                    b.latitude, b.longitude, b.heading, b.fix_type,
                    b.stop_id, b.next_stop_id, b.code, b.recorded_at,
                    r.route_id, r.route_long_name,
                    t.trip_id, t.trip_headsign,
                    st_curr.stop_sequence   AS bus_seq,
                    st_target.stop_sequence AS target_seq,
                    (st_target.stop_sequence - st_curr.stop_sequence) AS stops_away,
                    'curr'::text AS match_source
                  FROM latest_per_busish b
                  JOIN routes r           ON r.route_short_name = b.route
                  JOIN gtfs_trips t       ON t.route_id = r.route_id
                  JOIN gtfs_versions v1   ON t.version_id = v1.id AND v1.is_active = TRUE
                  JOIN gtfs_stop_times st_curr
                                      ON st_curr.trip_id = t.trip_id
                                     AND st_curr.version_id = t.version_id
                                     AND st_curr.stop_id = b.stop_id
                  JOIN gtfs_stop_times st_target
                                      ON st_target.trip_id = t.trip_id
                                     AND st_target.version_id = t.version_id
                                     AND st_target.stop_id = %s
                  WHERE b.stop_id IS NOT NULL
                    AND st_target.stop_sequence >= st_curr.stop_sequence
                ),
                combined AS (
                  SELECT * FROM matched_by_next
                  UNION ALL
                  SELECT * FROM matched_by_curr
                ),
                ranked AS (
                  SELECT
                    c.*,
                    ROW_NUMBER() OVER (
                      PARTITION BY c.bus_id
                      ORDER BY c.stops_away ASC, c.match_source = 'next' DESC
                    ) AS rn
                  FROM combined c
                  WHERE c.stops_away >= 0
                ),
                picked AS (
                  SELECT *
                  FROM ranked
                  WHERE rn = 1
                ),
                chain(bs_id, cur_id, depth) AS (
                  SELECT p.bus_id, p.bus_id, 0
                  FROM picked p
                  UNION ALL
                  SELECT c.bs_id, bs.linked_id, c.depth + 1
                  FROM chain c
                  JOIN bus_status bs ON bs.id = c.cur_id
                  WHERE bs.linked_id IS NOT NULL
                    AND c.depth < 200
                ),
                delays_join AS (
                  SELECT
                    c.bs_id,
                    c.depth,
                    bd.bus_status_id,
                    bd.route_id      AS delay_route_id,
                    bd.stop_id       AS delay_stop_id,
                    bd.scheduled_arrival_time,
                    bd.actual_arrival_time,
                    bd.delay_seconds,
                    bd.recorded_at   AS delay_recorded_at,
                    bd.gtfs_version_id
                  FROM chain c
                  JOIN bus_delays bd ON bd.bus_status_id = c.cur_id
                ),
                latest_delay_per_bus AS (
                  SELECT DISTINCT ON (bs_id)
                         *
                  FROM delays_join
                  ORDER BY bs_id, depth ASC
                )
                SELECT
                  p.bus_id               AS id,
                  p.route,
                  p.latitude, p.longitude, p.heading, p.fix_type,
                  p.stop_id, p.next_stop_id, p.code, p.recorded_at,
                  p.route_id, p.route_long_name,
                  p.trip_id, p.trip_headsign,
                  p.bus_seq, p.target_seq,
                  p.stops_away,
                  p.match_source,
                  ld.delay_stop_id,
                  ld.scheduled_arrival_time,
                  ld.actual_arrival_time,
                  ld.delay_seconds,
                  ld.delay_recorded_at,
                  ld.gtfs_version_id
                FROM picked p
                LEFT JOIN latest_delay_per_bus ld
                       ON ld.bs_id = p.bus_id
                       AND (ld.delay_route_id::text = p.route::text)
                ORDER BY p.route, p.stops_away, p.recorded_at DESC
            """, (station['stop_id'], station['stop_id']))

            buses = cursor.fetchall()
            for bus in buses:
                bus_dict = dict(bus)
                bus_dict['station_id'] = station['stop_id']
                bus_dict['station_name'] = station['stop_name']
                all_buses.append(bus_dict)

        return jsonify({
            'station_name': station_name,
            'stations': [dict(s) for s in stations],
            'approaching_buses': all_buses,
            'stations_count': len(stations)
        })

    except Exception as e:
        logger.error(f"Error getting station name buses: {e}")
        return jsonify({'error': t('ERROR_DATABASE')}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/station/<stop_id>/trips/debug')
def station_trips_debug(stop_id):
    """Debug version to see what's happening with trip filtering."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # First, check if station exists
        cursor.execute("""
            SELECT COUNT(*) as count FROM gtfs_stops s
            JOIN gtfs_versions v ON s.version_id = v.id
            WHERE v.is_active = TRUE AND s.stop_id = %s
        """, (stop_id,))

        station_count = cursor.fetchone()['count']

        # Check basic trips without calendar filtering
        cursor.execute("""
            SELECT COUNT(*) as trip_count FROM gtfs_stop_times st
            JOIN gtfs_versions v ON st.version_id = v.id
            WHERE v.is_active = TRUE AND st.stop_id = %s
        """, (stop_id,))

        basic_trip_count = cursor.fetchone()['trip_count']

        # Check available service_ids
        cursor.execute("""
            SELECT DISTINCT t.service_id
            FROM gtfs_stop_times st
            JOIN gtfs_trips t ON st.trip_id = t.trip_id AND st.version_id = t.version_id
            JOIN gtfs_versions v ON st.version_id = v.id
            WHERE v.is_active = TRUE AND st.stop_id = %s
            LIMIT 10
        """, (stop_id,))

        service_ids = [row['service_id'] for row in cursor.fetchall()]

        # Check calendar table structure
        cursor.execute("""
            SELECT * FROM gtfs_calendar
            JOIN gtfs_versions v ON gtfs_calendar.version_id = v.id
            WHERE v.is_active = TRUE
            LIMIT 3
        """)

        calendar_sample = cursor.fetchall()

        # Check calendar_dates structure
        cursor.execute("""
            SELECT * FROM gtfs_calendar_dates
            JOIN gtfs_versions v ON gtfs_calendar_dates.version_id = v.id
            WHERE v.is_active = TRUE
            LIMIT 3
        """)

        calendar_dates_sample = cursor.fetchall()

        return jsonify({
            'stop_id': stop_id,
            'station_exists': station_count > 0,
            'basic_trip_count': basic_trip_count,
            'service_ids': service_ids,
            'calendar_sample': [dict(row) for row in calendar_sample],
            'calendar_dates_sample': [dict(row) for row in calendar_dates_sample],
            'today': datetime.now(timezone.utc).date().isoformat()
        })

    except Exception as e:
        logger.error(f"Debug error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        return_db_connection(conn)

@app.route('/analytics')
def analytics():
    """Analytics dashboard."""
    return render_template('analytics.html')


if __name__ == '__main__':
    init_db_pool()

    # Note: Background monitoring is automatically started by gunicorn.conf.py when running in production
    # This block only runs when testing locally with `python app.py`

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)