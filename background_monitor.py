#!/usr/bin/env python3

import threading
import time
import logging
import os
from bus_monitor_pg import BusMonitor

logger = logging.getLogger(__name__)

class BackgroundBusMonitor:
    """Background thread for bus monitoring."""

    def __init__(self, interval=15):
        self.interval = interval
        self.monitor = None
        self.thread = None
        self.running = False
        self.database_url = os.environ.get('DATABASE_URL')

    def start(self):
        """Start the background monitoring thread."""
        if self.running:
            logger.warning("Background monitor already running")
            return

        if not self.database_url:
            logger.error("DATABASE_URL not configured, cannot start background monitor")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Background bus monitor started")

    def stop(self):
        """Stop the background monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Background bus monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop running in background thread."""
        try:
            self.monitor = BusMonitor(self.database_url)
            logger.info(f"Background monitor initialized with {self.interval}s interval")

            iteration = 0
            while self.running:
                try:
                    iteration += 1
                    logger.info(f"Background monitoring iteration #{iteration}")
                    success = self.monitor.run_once()

                    if success:
                        logger.info(f"Background iteration #{iteration} completed successfully")
                    else:
                        logger.warning(f"Background iteration #{iteration} failed")

                    # Sleep in small chunks so we can stop quickly
                    for _ in range(self.interval):
                        if not self.running:
                            break
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"Error in background monitoring iteration #{iteration}: {e}")
                    # Sleep before retrying
                    for _ in range(min(30, self.interval)):
                        if not self.running:
                            break
                        time.sleep(1)

        except Exception as e:
            logger.error(f"Background monitor failed to start: {e}")
            self.running = False

    def is_running(self):
        """Check if the background monitor is running."""
        return self.running and self.thread and self.thread.is_alive()

    def get_status(self):
        """Get status information about the background monitor."""
        return {
            'running': self.is_running(),
            'interval': self.interval,
            'database_configured': bool(self.database_url)
        }

# Global instance
background_monitor = BackgroundBusMonitor()