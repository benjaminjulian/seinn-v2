#!/usr/bin/env python3

import os
import sys
import logging
from bus_monitor_pg import BusMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bus_monitor():
    """Test the bus monitoring functionality."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False

    try:
        logger.info("Creating BusMonitor instance...")
        monitor = BusMonitor(database_url)

        logger.info("Testing API connection...")
        root = monitor.fetch_and_parse_xml()
        if root is None:
            logger.error("Failed to fetch XML data from API")
            return False

        bus_elements = root.findall('bus')
        logger.info(f"Found {len(bus_elements)} bus records in API response")

        if len(bus_elements) == 0:
            logger.warning("No bus data available from API")
            return True

        logger.info("Testing database insertion...")
        records_added = monitor.store_bus_data(bus_elements)
        logger.info(f"Added {records_added} records to database")

        if records_added > 0:
            logger.info("Testing speed calculation...")
            speeds_calculated = monitor.calculate_speeds_for_recent_data()
            logger.info(f"Calculated speeds for {speeds_calculated} records")

            logger.info("Testing delay calculation...")
            delays_calculated = monitor.detect_stop_arrivals_and_calculate_delays()
            logger.info(f"Calculated delays for {delays_calculated} arrivals")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Testing Bus Monitor...")
    success = test_bus_monitor()
    if success:
        logger.info("✅ Bus monitor test completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Bus monitor test failed")
        sys.exit(1)