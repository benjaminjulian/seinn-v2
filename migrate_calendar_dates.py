#!/usr/bin/env python3

import os
import sys
import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Add gtfs_calendar_dates table to existing database."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info("Adding gtfs_calendar_dates table...")

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'gtfs_calendar_dates'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if table_exists:
            logger.info("gtfs_calendar_dates table already exists, skipping creation")
            conn.close()
            return

        # Create the table
        cursor.execute('''
            CREATE TABLE gtfs_calendar_dates (
                version_id INTEGER NOT NULL,
                service_id TEXT NOT NULL,
                date TEXT NOT NULL,
                exception_type INTEGER NOT NULL,
                FOREIGN KEY (version_id) REFERENCES gtfs_versions (id),
                PRIMARY KEY (version_id, service_id, date)
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("gtfs_calendar_dates table created successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()