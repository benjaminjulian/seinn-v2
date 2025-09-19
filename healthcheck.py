#!/usr/bin/env python3

import os
import sys
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check database connectivity and table existence."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not set")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check if required tables exist
        required_tables = ['bus_status', 'gtfs_stops', 'gtfs_routes', 'gtfs_versions']

        for table in required_tables:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = %s
            """, (table,))

            if cursor.fetchone()[0] == 0:
                logger.error(f"Required table '{table}' does not exist")
                return False

        # Check if we have any GTFS data
        cursor.execute("SELECT COUNT(*) FROM gtfs_versions WHERE is_active = TRUE")
        if cursor.fetchone()[0] == 0:
            logger.warning("No active GTFS version found")
            return False

        cursor.execute("SELECT COUNT(*) FROM gtfs_stops")
        stop_count = cursor.fetchone()[0]
        logger.info(f"Database healthy: {stop_count} stops loaded")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

def main():
    if check_database():
        logger.info("✅ Database health check passed")
        sys.exit(0)
    else:
        logger.error("❌ Database health check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()