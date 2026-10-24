import multiprocessing
import os

# Hosts like Render choose the port and pass it in $PORT; Docker / VPS setups use 8000.
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
# WEB_CONCURRENCY keeps small instances (Render free: 512 MB) from starting more workers than fit in memory.
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 5)))
threads = 2
timeout = 60
accesslog = "-"
errorlog = "-"
