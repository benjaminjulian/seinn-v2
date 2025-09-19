#!/usr/bin/env python3

import os
import sys
import logging
from bus_monitor_pg import BusMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Initialize the database and optionally download GTFS data."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info("Initializing database...")

    try:
        # Create BusMonitor instance which will initialize the database
        monitor = BusMonitor(database_url)
        logger.info("Database schema created successfully")

        # Download initial GTFS data
        logger.info("Downloading initial GTFS data...")
        if monitor.download_and_update_gtfs():
            logger.info("GTFS data downloaded and loaded successfully")
        else:
            logger.warning("Failed to download GTFS data, but database is initialized")

        logger.info("Database initialization complete!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()