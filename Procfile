release: python init_db.py
web: gunicorn app:app
worker: python bus_monitor_pg.py