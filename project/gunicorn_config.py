from multiprocessing import cpu_count
from os import environ


def max_workers():    
    return cpu_count()


reload = True
daemon = False
bind = '0.0.0.0:5000'
loglevel = 'debug'
log_file='/var/log/gunicorn.log'
accesslog = '/var/log/gunicorn.log'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = '/var/log/gunicorn.log'
workers = max_workers()
threads = 4
timeout = 60
worker_temp_dir = '/dev/shm'
# pidfile = '/srv/elc-production/run/gunicorn.elc-production.pid'

