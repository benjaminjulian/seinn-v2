#!/usr/bin/env python3

import os
import sys
import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate existing database to fix data type issues."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info("Starting database migration...")

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check if bus_status table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'bus_status'
            )
        """)

        table_exists = cursor.fetchone()[0]

        if not table_exists:
            logger.info("bus_status table doesn't exist, no migration needed")
            conn.close()
            return

        # Get current column types
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'bus_status'
            AND column_name IN ('latitude', 'longitude', 'heading', 'speed_kmh')
        """)

        columns = cursor.fetchall()
        logger.info(f"Current column types: {columns}")

        # Check if we need to migrate from REAL to DOUBLE PRECISION
        needs_migration = any(col[1] == 'real' for col in columns)

        if needs_migration:
            logger.info("Migrating numeric columns from REAL to DOUBLE PRECISION...")

            # Alter column types
            numeric_columns = ['latitude', 'longitude', 'heading', 'speed_kmh']
            for col in numeric_columns:
                logger.info(f"Migrating column {col}...")
                cursor.execute(f"""
                    ALTER TABLE bus_status
                    ALTER COLUMN {col} TYPE DOUBLE PRECISION
                    USING {col}::DOUBLE PRECISION
                """)

            # Similarly for gtfs_stops
            logger.info("Migrating gtfs_stops table...")
            cursor.execute("""
                ALTER TABLE gtfs_stops
                ALTER COLUMN stop_lat TYPE DOUBLE PRECISION
                USING stop_lat::DOUBLE PRECISION
            """)
            cursor.execute("""
                ALTER TABLE gtfs_stops
                ALTER COLUMN stop_lon TYPE DOUBLE PRECISION
                USING stop_lon::DOUBLE PRECISION
            """)

            conn.commit()
            logger.info("Database migration completed successfully")
        else:
            logger.info("No migration needed - columns already use correct types")

        conn.close()

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()