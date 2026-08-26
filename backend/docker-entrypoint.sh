#!/bin/sh
set -e

echo "Waiting for database at ${DB_HOST:-db}:${DB_PORT:-5432}..."
until python -c "
import socket, os, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((os.environ.get('DB_HOST', 'db'), int(os.environ.get('DB_PORT', 5432))))
    s.close()
except Exception:
    sys.exit(1)
"; do
  sleep 1
done
echo "Database is up."

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Seed race + vendor categories on first boot (idempotent — updates in
# place rather than duplicating on every restart).
python manage.py seed_categories || true
python manage.py seed_vendor_categories || true

exec "$@"
