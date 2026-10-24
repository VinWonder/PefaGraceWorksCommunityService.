import multiprocessing

bind = "0.0.0.0:8000"
workers = min(multiprocessing.cpu_count() * 2 + 1, 5)
threads = 2
timeout = 60
accesslog = "-"
errorlog = "-"
