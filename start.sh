#!/usr/bin/env bash
# Container start: prepare the database, then serve. Used by the Dockerfile (Railway, Docker, VPS).
set -o errexit

python manage.py migrate --noinput

# A fresh database gets the organisation profile; set SEED_DEMO=1 to add sample events too.
# Later starts skip this so admin edits are never overwritten.
python manage.py seed_pgcs --if-empty ${SEED_DEMO:+--demo}

# Admin login from DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD, if set and not created yet.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py createsuperuser --noinput 2>/dev/null || echo "Admin user already exists."
fi

exec gunicorn config.wsgi:application -c gunicorn.conf.py
