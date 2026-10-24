#!/usr/bin/env bash
# Render build step: install, collect static files, migrate, and load content on a fresh database.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# First deploy only: load the organisation profile and sample events. Later deploys leave admin edits alone.
python manage.py seed_pgcs --demo --if-empty

# Admin login from DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD, if set and not created yet.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py createsuperuser --noinput 2>/dev/null || echo "Admin user already exists."
fi
