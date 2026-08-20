#!/usr/bin/env bash
set -euo pipefail

# Restores a .sql.gz dump produced by backup-db.sh into the running
# production db container.
#
# DESTRUCTIVE: drops and recreates the target database before loading the
# dump. Prompts for confirmation before touching anything.
#
# Usage:
#   ./infra/restore-db.sh /home/ubuntu/db-backups/siavonga_run_20260101_030000.sql.gz
#
# To restore from S3 instead of a local file:
#   aws s3 cp s3://<bucket>/siavonga_run_20260101_030000.sql.gz /tmp/restore.sql.gz
#   ./infra/restore-db.sh /tmp/restore.sql.gz

if [ $# -ne 1 ]; then
  echo "Usage: $0 <backup-file.sql.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"
[ -f "$BACKUP_FILE" ] || { echo "File not found: $BACKUP_FILE" >&2; exit 1; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

set -a
source .env.prod
set +a

echo "This will DROP and recreate database '$DB_NAME' with the contents of:"
echo "  $BACKUP_FILE"
read -r -p "Type 'yes' to continue: " CONFIRM
[ "$CONFIRM" = "yes" ] || { echo "Aborted."; exit 1; }

docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" \
  -c "CREATE DATABASE \"$DB_NAME\";"

gunzip -c "$BACKUP_FILE" | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1

echo "Restore complete. Restart the backend so it doesn't hold stale connections:"
echo "  docker compose --env-file .env.prod -f docker-compose.prod.yml restart backend"
