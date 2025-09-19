#!/usr/bin/env python3

import psycopg2
import psycopg2.extras
import requests
import xml.etree.ElementTree as ET
import time
import logging
import math
import zipfile
import io
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bus linking configuration
V_GATE_KMH = 120.0      # reachability gate (not a cap)
R_BUFFER_M = 120.0      # extra radius to allow GPS jitter

# Speed calculation helper functions
def parse_bus_time(s):
    """Parse YYMMDDHHMMSS format to UTC datetime object."""
    if not s or len(s) != 12 or not s.isdigit():
        return None
    # Bus timestamps are in GMT/UTC
    return datetime.strptime("20"+s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)

def parse_iso(ts):
    """Parse recorded_at timestamp to epoch seconds."""
    return int(datetime.fromisoformat(ts).timestamp())

def haversine_m(a_lat, a_lon, b_lat, b_lon):
    """Calculate haversine distance in meters."""
    R = 6371000.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dphi = math.radians(b_lat - a_lat)
    dl = math.radians(b_lon - a_lon)
    h = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def choose_dt_s(p, c):
    """Choose best time delta with hygiene rules."""
    bt_p, bt_c = parse_bus_time(p["time_yymmddhhmmss"]), parse_bus_time(c["time_yymmddhhmmss"])
    rt_p, rt_c = parse_iso(p["recorded_at"]), parse_iso(c["recorded_at"])
    dt_bus = (bt_c - bt_p).total_seconds() if (bt_p and bt_c) else None
    dt_rec = rt_c - rt_p
    # prefer recorded_at only if bus delta is invalid or disagrees massively
    if dt_bus is None or dt_bus <= 0 or abs(dt_bus - dt_rec) > 60:
        return dt_rec
    return dt_bus

class BusMonitor:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        self.url = "https://opendata.straeto.is/bus/x8061285850508698/status.xml"
        self.gtfs_url = "https://opendata.straeto.is/data/gtfs/gtfs.zip"
        self.init_database()

    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.database_url)

    def init_database(self):
        """Initialize the PostgreSQL database with the required schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bus_status (
                id SERIAL PRIMARY KEY,
                timestamp_str TEXT NOT NULL,
                time_yymmddhhmmss TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                heading REAL NOT NULL,
                fix_type INTEGER NOT NULL,
                route TEXT NOT NULL,
                stop_id TEXT,
                next_stop_id TEXT,
                code TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                time_hhmm TEXT NOT NULL,
                recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                speed_kmh REAL,
                linked_id INTEGER,
                UNIQUE(time_yymmddhhmmss, latitude, longitude, route)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_route_time ON bus_status(route, time_hhmm)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_day_time ON bus_status(day_of_week, time_hhmm)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recorded_at ON bus_status(recorded_at)
        ''')

        # GTFS tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gtfs_versions (
                id SERIAL PRIMARY KEY,
                hash TEXT UNIQUE NOT NULL,
                downloaded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gtfs_stops (
                version_id INTEGER NOT NULL,
                stop_id TEXT NOT NULL,
                stop_name TEXT,
                stop_lat REAL,
                stop_lon REAL,
                zone_id TEXT,
                stop_code TEXT,
                FOREIGN KEY (version_id) REFERENCES gtfs_versions (id),
                PRIMARY KEY (version_id, stop_id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_gtfs_stops_name ON gtfs_stops(stop_name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_gtfs_stops_code ON gtfs_stops(stop_code)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_gtfs_stops_location ON gtfs_stops(stop_lat, stop_lon)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gtfs_routes (
                version_id INTEGER NOT NULL,
                route_id TEXT NOT NULL,
                route_short_name TEXT,
                route_long_name TEXT,
                route_type INTEGER,
                FOREIGN KEY (version_id) REFERENCES gtfs_versions (id),
                PRIMARY KEY (version_id, route_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gtfs_trips (
                version_id INTEGER NOT NULL,
                trip_id TEXT NOT NULL,
                route_id TEXT NOT NULL,
                service_id TEXT NOT NULL,
                trip_headsign TEXT,
                direction_id INTEGER,
                FOREIGN KEY (version_id) REFERENCES gtfs_versions (id),
                PRIMARY KEY (version_id, trip_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gtfs_stop_times (
                version_id INTEGER NOT NULL,
                trip_id TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                stop_id TEXT NOT NULL,
                stop_sequence INTEGER NOT NULL,
                FOREIGN KEY (version_id) REFERENCES gtfs_versions (id),
                PRIMARY KEY (version_id, trip_id, stop_sequence)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stop_times_stop ON gtfs_stop_times(version_id, stop_id)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gtfs_calendar (
                version_id INTEGER NOT NULL,
                service_id TEXT NOT NULL,
                monday INTEGER NOT NULL,
                tuesday INTEGER NOT NULL,
                wednesday INTEGER NOT NULL,
                thursday INTEGER NOT NULL,
                friday INTEGER NOT NULL,
                saturday INTEGER NOT NULL,
                sunday INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                FOREIGN KEY (version_id) REFERENCES gtfs_versions (id),
                PRIMARY KEY (version_id, service_id)
            )
        ''')

        # Delay tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bus_delays (
                id SERIAL PRIMARY KEY,
                bus_status_id INTEGER NOT NULL,
                route_id TEXT NOT NULL,
                stop_id TEXT NOT NULL,
                scheduled_arrival_time TEXT NOT NULL,
                actual_arrival_time TIMESTAMP WITH TIME ZONE NOT NULL,
                delay_seconds INTEGER NOT NULL,
                recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                gtfs_version_id INTEGER,
                FOREIGN KEY (bus_status_id) REFERENCES bus_status (id),
                FOREIGN KEY (gtfs_version_id) REFERENCES gtfs_versions (id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_delays_route_time ON bus_delays(route_id, actual_arrival_time)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_delays_stop_time ON bus_delays(stop_id, actual_arrival_time)
        ''')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def parse_time_components(self, time_str: str) -> tuple[int, str]:
        """
        Parse YYMMDDHHMMSS format and extract day of week and HHMM.
        Returns (day_of_week, hhmm_str) where day_of_week: 0=Monday, 6=Sunday
        """
        if len(time_str) != 12:
            raise ValueError(f"Invalid time format: {time_str}")

        year = int("20" + time_str[:2])
        month = int(time_str[2:4])
        day = int(time_str[4:6])
        hour = int(time_str[6:8])
        minute = int(time_str[8:10])

        dt = datetime(year, month, day, hour, minute)
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        hhmm = time_str[6:10]

        return day_of_week, hhmm

    def fetch_and_parse_xml(self) -> Optional[ET.Element]:
        """Fetch XML data from the API and parse it."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.text)
            return root
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return None

    def store_bus_data(self, bus_elements: list):
        """Store bus data in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        records_added = 0
        recorded_at = datetime.now(timezone.utc)

        for bus in bus_elements:
            try:
                time_str = bus.get('time')
                lat = float(bus.get('lat'))
                lon = float(bus.get('lon'))
                head = float(bus.get('head'))
                fix_type = int(bus.get('fix'))
                route = bus.get('route')
                stop_id = bus.get('stop') or None
                next_stop_id = bus.get('next') or None
                code = bus.get('code')

                day_of_week, hhmm = self.parse_time_components(time_str)

                cursor.execute('''
                    INSERT INTO bus_status
                    (timestamp_str, time_yymmddhhmmss, latitude, longitude, heading,
                     fix_type, route, stop_id, next_stop_id, code, day_of_week,
                     time_hhmm, recorded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (time_yymmddhhmmss, latitude, longitude, route) DO NOTHING
                ''', (
                    bus.get('time'), time_str, lat, lon, head, fix_type,
                    route, stop_id, next_stop_id, code, day_of_week, hhmm, recorded_at
                ))

                if cursor.rowcount > 0:
                    records_added += 1

            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid bus record: {e}")
                continue

        conn.commit()
        conn.close()

        logger.info(f"Added {records_added} new records to database")
        return records_added

    def calculate_speeds_for_recent_data(self):
        """Calculate speeds for the most recent batch using improved linking algorithm."""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get the most recent batch
            cursor.execute("""
                SELECT MAX(recorded_at) as latest_batch
                FROM bus_status
            """)
            result = cursor.fetchone()
            latest_batch = result["latest_batch"] if result else None

            if not latest_batch:
                return 0

            # Find previous batch
            cursor.execute("""
                SELECT MAX(recorded_at) as prev_batch
                FROM bus_status
                WHERE recorded_at < %s
            """, (latest_batch,))
            prev_batch_result = cursor.fetchone()
            prev_batch = prev_batch_result["prev_batch"] if prev_batch_result else None

            if not prev_batch:
                logger.info("No previous batch found for linking")
                return 0

            # Load batches
            cols = """id, latitude, longitude, heading, fix_type, route,
                      stop_id, next_stop_id, code, time_yymmddhhmmss,
                      EXTRACT(EPOCH FROM recorded_at) as recorded_at_epoch"""

            cursor.execute(
                f"SELECT {cols} FROM bus_status WHERE recorded_at = %s",
                (prev_batch,)
            )
            prev_rows = cursor.fetchall()

            cursor.execute(
                f"SELECT {cols} FROM bus_status WHERE recorded_at = %s",
                (latest_batch,)
            )
            curr_rows = cursor.fetchall()

            # Convert to format expected by linking algorithm
            def convert_row(row):
                r = dict(row)
                r["recorded_at"] = datetime.fromtimestamp(r["recorded_at_epoch"], tz=timezone.utc).isoformat()
                return r

            prev_rows = [convert_row(r) for r in prev_rows]
            curr_rows = [convert_row(r) for r in curr_rows]

            by_route_prev = defaultdict(list)
            by_route_curr = defaultdict(list)
            for r in prev_rows:
                by_route_prev[r["route"]].append(r)
            for r in curr_rows:
                by_route_curr[r["route"]].append(r)

            # Build gated candidates and annotate continuity
            gate_mps = V_GATE_KMH / 3.6
            candidates_by_route = defaultdict(list)

            for route, curr_list in by_route_curr.items():
                prev_list = by_route_prev.get(route, [])
                if not prev_list:
                    continue
                for c in curr_list:
                    for p in prev_list:
                        dt = choose_dt_s(p, c)
                        if dt is None or dt <= 0:
                            continue
                        dist = haversine_m(p["latitude"], p["longitude"], c["latitude"], c["longitude"])
                        # reachability gate
                        if dist > gate_mps * dt + R_BUFFER_M:
                            continue
                        spd = (dist / dt) * 3.6
                        cont = 0.0
                        if p["stop_id"] and c["stop_id"] and p["stop_id"] == c["stop_id"]:
                            cont = 1.0
                        elif p["next_stop_id"] and c["next_stop_id"] and p["next_stop_id"] == c["next_stop_id"]:
                            cont = 0.8
                        elif p["next_stop_id"] and c["stop_id"] and p["next_stop_id"] == c["stop_id"]:
                            cont = 0.6
                        candidates_by_route[route].append({
                            "speed": spd, "dist": dist, "dt": dt,
                            "prev_id": p["id"], "curr_id": c["id"],
                            "continuity": cont
                        })

            # Mutual-nearest filter per route
            chosen_updates = []
            for route, edges in candidates_by_route.items():
                if not edges:
                    continue

                # Build best-by-prev and best-by-curr maps
                best_for_prev = {}
                best_for_curr = {}
                for e in edges:
                    pid, cid, s = e["prev_id"], e["curr_id"], e["speed"]
                    if pid not in best_for_prev or s < best_for_prev[pid]["speed"]:
                        best_for_prev[pid] = e
                    if cid not in best_for_curr or s < best_for_curr[cid]["speed"]:
                        best_for_curr[cid] = e

                # Keep only mutual nearest; sort by (continuity desc, speed asc)
                mutual = []
                for e in edges:
                    pid, cid = e["prev_id"], e["curr_id"]
                    if best_for_prev.get(pid) is e and best_for_curr.get(cid) is e:
                        mutual.append(e)
                mutual.sort(key=lambda e: (-e["continuity"], e["speed"]))

                used_prev, used_curr = set(), set()
                for e in mutual:
                    pid, cid = e["prev_id"], e["curr_id"]
                    if pid in used_prev or cid in used_curr:
                        continue
                    used_prev.add(pid)
                    used_curr.add(cid)
                    chosen_updates.append((cid, pid, e["speed"]))

            # Apply updates
            # Clean slate for current batch
            cursor.execute("""UPDATE bus_status
                              SET linked_id = NULL, speed_kmh = NULL
                              WHERE recorded_at = %s""", (latest_batch,))

            # Write chosen matches
            if chosen_updates:
                cursor.executemany("""UPDATE bus_status
                                      SET linked_id = %s, speed_kmh = %s
                                      WHERE id = %s""", chosen_updates)

            conn.commit()

            logger.info(f"Batch {prev_batch} → {latest_batch}: "
                       f"{len(chosen_updates)} matches written; "
                       f"{len(curr_rows)-len(chosen_updates)} current rows left NULL.")

            return len(chosen_updates)

        finally:
            conn.close()

    def download_and_update_gtfs(self) -> bool:
        """Download GTFS data if it has changed and update database."""
        try:
            # Download GTFS zip file
            logger.info("Downloading GTFS data...")
            response = requests.get(self.gtfs_url, timeout=30)
            response.raise_for_status()

            # Calculate hash to check if data has changed
            gtfs_hash = hashlib.sha256(response.content).hexdigest()

            conn = self.get_connection()
            cursor = conn.cursor()

            # Check if we already have this version
            cursor.execute("SELECT id FROM gtfs_versions WHERE hash = %s", (gtfs_hash,))
            existing_version = cursor.fetchone()

            if existing_version:
                logger.info("GTFS data unchanged, skipping update")
                # Ensure this version is marked as active
                cursor.execute("UPDATE gtfs_versions SET is_active = FALSE")
                cursor.execute("UPDATE gtfs_versions SET is_active = TRUE WHERE hash = %s", (gtfs_hash,))
                conn.commit()
                conn.close()
                return True

            logger.info("New GTFS data detected, updating database...")

            # Create new version entry
            cursor.execute(
                "INSERT INTO gtfs_versions (hash, downloaded_at) VALUES (%s, %s) RETURNING id",
                (gtfs_hash, datetime.now(timezone.utc))
            )
            version_id = cursor.fetchone()[0]

            # Mark all other versions as inactive
            cursor.execute("UPDATE gtfs_versions SET is_active = FALSE WHERE id != %s", (version_id,))

            # Parse GTFS zip file
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                self._parse_gtfs_file(zf, 'stops.txt', cursor, version_id, self._insert_stops)
                self._parse_gtfs_file(zf, 'routes.txt', cursor, version_id, self._insert_routes)
                self._parse_gtfs_file(zf, 'trips.txt', cursor, version_id, self._insert_trips)
                self._parse_gtfs_file(zf, 'stop_times.txt', cursor, version_id, self._insert_stop_times)
                self._parse_gtfs_file(zf, 'calendar.txt', cursor, version_id, self._insert_calendar)

            conn.commit()
            conn.close()

            logger.info(f"GTFS data updated successfully (version {version_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to update GTFS data: {e}")
            return False

    def _parse_gtfs_file(self, zf, filename, cursor, version_id, insert_func):
        """Parse a single GTFS file from the zip archive."""
        try:
            with zf.open(filename) as f:
                lines = f.read().decode('utf-8-sig').strip().split('\n')
                if not lines:
                    return

                headers = lines[0].split(',')
                for line in lines[1:]:
                    if line.strip():
                        values = line.split(',')
                        row = dict(zip(headers, values))
                        insert_func(cursor, version_id, row)

        except KeyError:
            logger.warning(f"GTFS file {filename} not found in archive")

    def _insert_stops(self, cursor, version_id, row):
        """Insert stop data."""
        cursor.execute('''
            INSERT INTO gtfs_stops
            (version_id, stop_id, stop_name, stop_lat, stop_lon, zone_id, stop_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (version_id, stop_id) DO UPDATE SET
                stop_name = EXCLUDED.stop_name,
                stop_lat = EXCLUDED.stop_lat,
                stop_lon = EXCLUDED.stop_lon,
                zone_id = EXCLUDED.zone_id,
                stop_code = EXCLUDED.stop_code
        ''', (
            version_id,
            row.get('stop_id', '').strip('"'),
            row.get('stop_name', '').strip('"'),
            float(row.get('stop_lat', 0)) if row.get('stop_lat') else None,
            float(row.get('stop_lon', 0)) if row.get('stop_lon') else None,
            row.get('zone_id', '').strip('"') or None,
            row.get('stop_code', '').strip('"') or None
        ))

    def _insert_routes(self, cursor, version_id, row):
        """Insert route data."""
        cursor.execute('''
            INSERT INTO gtfs_routes
            (version_id, route_id, route_short_name, route_long_name, route_type)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (version_id, route_id) DO UPDATE SET
                route_short_name = EXCLUDED.route_short_name,
                route_long_name = EXCLUDED.route_long_name,
                route_type = EXCLUDED.route_type
        ''', (
            version_id,
            row.get('route_id', '').strip('"'),
            row.get('route_short_name', '').strip('"'),
            row.get('route_long_name', '').strip('"'),
            int(row.get('route_type', 0)) if row.get('route_type') else None
        ))

    def _insert_trips(self, cursor, version_id, row):
        """Insert trip data."""
        cursor.execute('''
            INSERT INTO gtfs_trips
            (version_id, trip_id, route_id, service_id, trip_headsign, direction_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (version_id, trip_id) DO UPDATE SET
                route_id = EXCLUDED.route_id,
                service_id = EXCLUDED.service_id,
                trip_headsign = EXCLUDED.trip_headsign,
                direction_id = EXCLUDED.direction_id
        ''', (
            version_id,
            row.get('trip_id', '').strip('"'),
            row.get('route_id', '').strip('"'),
            row.get('service_id', '').strip('"'),
            row.get('trip_headsign', '').strip('"') or None,
            int(row.get('direction_id', 0)) if row.get('direction_id') else None
        ))

    def _insert_stop_times(self, cursor, version_id, row):
        """Insert stop time data."""
        cursor.execute('''
            INSERT INTO gtfs_stop_times
            (version_id, trip_id, arrival_time, departure_time, stop_id, stop_sequence)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (version_id, trip_id, stop_sequence) DO UPDATE SET
                arrival_time = EXCLUDED.arrival_time,
                departure_time = EXCLUDED.departure_time,
                stop_id = EXCLUDED.stop_id
        ''', (
            version_id,
            row.get('trip_id', '').strip('"'),
            row.get('arrival_time', '').strip('"'),
            row.get('departure_time', '').strip('"'),
            row.get('stop_id', '').strip('"'),
            int(row.get('stop_sequence', 0)) if row.get('stop_sequence') else 0
        ))

    def _insert_calendar(self, cursor, version_id, row):
        """Insert calendar data."""
        cursor.execute('''
            INSERT INTO gtfs_calendar
            (version_id, service_id, monday, tuesday, wednesday, thursday,
             friday, saturday, sunday, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (version_id, service_id) DO UPDATE SET
                monday = EXCLUDED.monday,
                tuesday = EXCLUDED.tuesday,
                wednesday = EXCLUDED.wednesday,
                thursday = EXCLUDED.thursday,
                friday = EXCLUDED.friday,
                saturday = EXCLUDED.saturday,
                sunday = EXCLUDED.sunday,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date
        ''', (
            version_id,
            row.get('service_id', '').strip('"'),
            int(row.get('monday', 0)),
            int(row.get('tuesday', 0)),
            int(row.get('wednesday', 0)),
            int(row.get('thursday', 0)),
            int(row.get('friday', 0)),
            int(row.get('saturday', 0)),
            int(row.get('sunday', 0)),
            row.get('start_date', '').strip('"'),
            row.get('end_date', '').strip('"')
        ))

    def should_update_gtfs(self) -> bool:
        """Check if GTFS should be updated (once per day)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(downloaded_at) FROM gtfs_versions")
        result = cursor.fetchone()
        last_download = result[0] if result else None
        conn.close()

        if not last_download:
            return True

        return datetime.now(timezone.utc) - last_download >= timedelta(days=1)

    def detect_stop_arrivals_and_calculate_delays(self):
        """Detect bus stop arrivals using linking data and calculate delays."""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get the most recent batch
            cursor.execute("SELECT MAX(recorded_at) as latest_batch FROM bus_status")
            result = cursor.fetchone()
            latest_batch = result["latest_batch"] if result else None

            if not latest_batch:
                return 0

            # Find previous batch
            cursor.execute("""
                SELECT MAX(recorded_at) as prev_batch
                FROM bus_status
                WHERE recorded_at < %s
            """, (latest_batch,))
            prev_batch_result = cursor.fetchone()
            prev_batch = prev_batch_result["prev_batch"] if prev_batch_result else None

            if not prev_batch:
                logger.info("No previous batch found for delay calculation")
                return 0

            # Find buses that have changed stops (indicating arrival)
            cursor.execute("""
                SELECT
                    curr.id as bus_status_id,
                    curr.route,
                    curr.stop_id as current_stop,
                    prev.stop_id as previous_stop,
                    curr.time_yymmddhhmmss,
                    curr.recorded_at,
                    curr.day_of_week
                FROM bus_status curr
                JOIN bus_status prev ON curr.linked_id = prev.id
                WHERE curr.recorded_at = %s
                AND prev.recorded_at = %s
                AND curr.stop_id IS NOT NULL
                AND prev.stop_id IS NOT NULL
                AND curr.stop_id != prev.stop_id
            """, (latest_batch, prev_batch))

            arrivals = cursor.fetchall()
            delays_calculated = 0

            # Get active GTFS version
            cursor.execute("SELECT id FROM gtfs_versions WHERE is_active = TRUE")
            gtfs_version_result = cursor.fetchone()
            if not gtfs_version_result:
                logger.warning("No active GTFS version found")
                return 0
            gtfs_version_id = gtfs_version_result["id"]

            for arrival in arrivals:
                delay_data = self._calculate_delay_for_arrival(cursor, arrival, gtfs_version_id)
                if delay_data:
                    cursor.execute('''
                        INSERT INTO bus_delays
                        (bus_status_id, route_id, stop_id, scheduled_arrival_time,
                         actual_arrival_time, delay_seconds, recorded_at, gtfs_version_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', delay_data)
                    delays_calculated += 1

            conn.commit()
            logger.info(f"Calculated delays for {delays_calculated} arrivals")
            return delays_calculated

        finally:
            conn.close()

    def _calculate_delay_for_arrival(self, cursor, arrival, gtfs_version_id):
        """Calculate delay for a specific bus arrival using bus system timestamp."""
        try:
            # Parse actual arrival time from bus system (GMT/UTC)
            actual_time_str = arrival["time_yymmddhhmmss"]
            if len(actual_time_str) != 12:
                return None

            # Use bus system timestamp (GMT/UTC) - this is critical!
            actual_dt = datetime.strptime("20" + actual_time_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            day_of_week = actual_dt.weekday()  # 0=Monday
            actual_time_hhmm = actual_time_str[6:10]
            actual_time_formatted = f"{actual_time_hhmm[:2]}:{actual_time_hhmm[2:]}:00"

            # Find matching GTFS schedule
            # Convert day_of_week to GTFS calendar format
            day_columns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_column = day_columns[day_of_week]

            # Find the closest scheduled arrival time
            cursor.execute(f"""
                WITH scheduled_times AS (
                    SELECT
                        st.arrival_time,
                        st.trip_id,
                        ABS(
                            EXTRACT(EPOCH FROM (st.arrival_time::time - %s::time))
                        ) AS time_diff_seconds
                    FROM gtfs_stop_times st
                    JOIN gtfs_trips t ON st.trip_id = t.trip_id AND st.version_id = t.version_id
                    JOIN gtfs_calendar c ON t.service_id = c.service_id AND t.version_id = c.version_id
                    WHERE st.version_id = %s
                    AND st.stop_id = %s
                    AND t.route_id = %s
                    AND c.{day_column} = 1
                )
                SELECT arrival_time, trip_id
                FROM scheduled_times
                WHERE time_diff_seconds <= 1800  -- Within 30 minutes
                ORDER BY time_diff_seconds ASC
                LIMIT 1
            """, (actual_time_formatted, gtfs_version_id, arrival["current_stop"], arrival["route"]))

            scheduled_result = cursor.fetchone()
            if not scheduled_result:
                return None

            scheduled_time_str = scheduled_result["arrival_time"]

            # Parse scheduled time (HH:MM:SS format)
            scheduled_time_parts = scheduled_time_str.split(':')
            if len(scheduled_time_parts) != 3:
                return None

            scheduled_hour = int(scheduled_time_parts[0])
            scheduled_minute = int(scheduled_time_parts[1])
            scheduled_second = int(scheduled_time_parts[2])

            # Handle times after midnight (25:00:00 format in GTFS)
            # Create scheduled datetime in UTC to match bus timestamp
            if scheduled_hour >= 24:
                scheduled_dt = actual_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                scheduled_dt = scheduled_dt.replace(
                    hour=scheduled_hour - 24,
                    minute=scheduled_minute,
                    second=scheduled_second
                )
            else:
                scheduled_dt = actual_dt.replace(
                    hour=scheduled_hour,
                    minute=scheduled_minute,
                    second=scheduled_second,
                    microsecond=0
                )

            # Calculate delay in seconds
            delay_seconds = int((actual_dt - scheduled_dt).total_seconds())

            return (
                arrival["bus_status_id"],
                arrival["route"],
                arrival["current_stop"],
                scheduled_time_str,
                actual_dt,
                delay_seconds,
                arrival["recorded_at"],
                gtfs_version_id
            )

        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Error calculating delay for arrival: {e}")
            return None

    def run_once(self) -> bool:
        """Run one iteration of data collection."""
        # Check if GTFS data should be updated (once per day)
        if self.should_update_gtfs():
            logger.info("Updating GTFS data...")
            if not self.download_and_update_gtfs():
                logger.error("Failed to update GTFS data, continuing with bus monitoring")

        logger.info("Fetching bus status data...")

        root = self.fetch_and_parse_xml()
        if root is None:
            return False

        bus_elements = root.findall('bus')
        if not bus_elements:
            logger.warning("No bus elements found in XML")
            return False

        logger.info(f"Found {len(bus_elements)} bus records")

        records_added = self.store_bus_data(bus_elements)

        # Calculate speeds for newly added data
        if records_added > 0:
            speeds_calculated = self.calculate_speeds_for_recent_data()
            if speeds_calculated > 0:
                logger.info(f"Linked and calculated speeds for {speeds_calculated} records")

                # Detect stop arrivals and calculate delays
                delays_calculated = self.detect_stop_arrivals_and_calculate_delays()
                if delays_calculated > 0:
                    logger.info(f"Calculated delays for {delays_calculated} bus arrivals")

        timestamp = root.get('timestamp', 'unknown')
        logger.info(f"Processed data from timestamp: {timestamp}")

        return True

    def run_continuous(self, interval: int = 15):
        """Run continuous monitoring with specified interval in seconds."""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        logger.info(f"Database URL configured: {'Yes' if self.database_url else 'No'}")

        iteration = 0
        while True:
            try:
                iteration += 1
                logger.info(f"Starting monitoring iteration #{iteration}")
                success = self.run_once()
                if success:
                    logger.info(f"Iteration #{iteration} completed successfully")
                else:
                    logger.warning(f"Iteration #{iteration} failed")

                logger.info(f"Sleeping for {interval} seconds...")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in iteration #{iteration}: {e}")
                import traceback
                traceback.print_exc()
                logger.info(f"Continuing after {interval} seconds...")
                time.sleep(interval)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Straeto Bus Monitor (PostgreSQL)")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once instead of continuously")
    parser.add_argument("--force-gtfs", action="store_true", help="Force GTFS data update")

    args = parser.parse_args()

    monitor = BusMonitor()

    if args.force_gtfs:
        print("Forcing GTFS data update...")
        if monitor.download_and_update_gtfs():
            print("GTFS data updated successfully")
        else:
            print("Failed to update GTFS data")
        return

    if args.once:
        success = monitor.run_once()
        exit(0 if success else 1)
    else:
        monitor.run_continuous(args.interval)

if __name__ == "__main__":
    print("Starting Straeto Bus Monitor...")
    print(f"DATABASE_URL configured: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")

    try:
        main()
    except KeyboardInterrupt:
        print("Bus monitor stopped by user")
    except Exception as e:
        print(f"Bus monitor failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)