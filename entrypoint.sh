#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

sleep 3

echo "Initializing database..."
python init_db.py

echo "Starting Flask app..."

gunicorn --workers 2 --threads 4 --timeout 120 -b 0.0.0.0:${PORT:-5000} app:app