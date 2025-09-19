import os
import logging

# Gunicorn configuration
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1  # Single worker to avoid multiple monitoring threads
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Initializing database and starting background monitoring...")

    try:
        # Initialize database first
        import os
        from bus_monitor_pg import BusMonitor

        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            server.log.error("DATABASE_URL environment variable not set")
            return

        server.log.info("Initializing database...")
        monitor = BusMonitor(database_url)
        server.log.info("Database schema created successfully")

        # Download initial GTFS data
        server.log.info("Downloading initial GTFS data...")
        if monitor.download_and_update_gtfs():
            server.log.info("GTFS data downloaded and loaded successfully")
        else:
            server.log.warning("Failed to download GTFS data, but database is initialized")

        server.log.info("Database initialization complete!")

        # Now start background monitoring
        from background_monitor import background_monitor
        background_monitor.start()
        server.log.info("Background bus monitoring started successfully")
    except Exception as e:
        server.log.error(f"Failed to initialize database or start background monitoring: {e}")

def worker_exit(server, worker):
    """Called just before a worker is exited."""
    try:
        from background_monitor import background_monitor
        background_monitor.stop()
        server.log.info("Background monitoring stopped")
    except:
        pass