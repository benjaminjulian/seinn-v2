#!/usr/bin/env python3

import os
import sys
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_database_initialized():
    """Ensure database is initialized before starting the web app."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bus_status'")
        table_exists = cursor.fetchone()[0] > 0
        conn.close()

        if not table_exists:
            logger.info("Database tables not found. Initializing...")

            # Import and run database initialization
            from bus_monitor_pg import BusMonitor
            monitor = BusMonitor(database_url)
            logger.info("Database schema created successfully")

            # Download GTFS data
            logger.info("Downloading initial GTFS data...")
            if monitor.download_and_update_gtfs():
                logger.info("GTFS data loaded successfully")
            else:
                logger.warning("GTFS data download failed")

        else:
            logger.info("Database tables already exist")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing anyway - web app will handle missing tables gracefully")

def main():
    """Initialize database then start the Flask app."""
    logger.info("Starting Straeto Bus Monitor...")

    ensure_database_initialized()

    logger.info("Starting Flask web application...")
    from app import app, init_db_pool

    # Initialize the connection pool
    init_db_pool()

    # Start the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()