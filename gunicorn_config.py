# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(multiprocessing.cpu_count() * 2 + 1)
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeout settings
timeout = 300  # 5 minutes for long transcription requests
keepalive = 5
graceful_timeout = 30

# Process naming
proc_name = 'stt_server'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Preloading app
preload_app = True

# Threading
threads = 4