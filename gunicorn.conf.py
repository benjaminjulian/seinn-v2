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
    server.log.info("Server is ready. Starting background monitoring...")

    try:
        from background_monitor import background_monitor
        background_monitor.start()
        server.log.info("Background bus monitoring started successfully")
    except Exception as e:
        server.log.error(f"Failed to start background monitoring: {e}")

def worker_exit(server, worker):
    """Called just before a worker is exited."""
    try:
        from background_monitor import background_monitor
        background_monitor.stop()
        server.log.info("Background monitoring stopped")
    except:
        pass