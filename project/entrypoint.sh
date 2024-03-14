#!/bin/sh

# echo "Starting server by Django wsgi";
# python manage.py run -h 0.0.0.0

echo "Starting server by Gunicorn wsgi";
# gunicorn -c gunicorn_config.py wsgi:app

exec "$@"
