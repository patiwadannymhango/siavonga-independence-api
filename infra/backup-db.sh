#!/usr/bin/env bash
set -euo pipefail

# Dumps the production Postgres database, keeps a rolling local window of
# backups, and — if BACKUP_S3_BUCKET is set in .env.prod — uploads a copy
# to S3 for offsite durability (protects against losing the server or its
# disk entirely, not just accidental data changes).
#
# Run from anywhere; it cd's into the project root itself. Meant to run on
# the server via cron, e.g. daily at 03:00:
#   0 3 * * * /home/ubuntu/siavonga-independence-api/infra/backup-db.sh >> /home/ubuntu/db-backups/backup.log 2>&1
#
# See infra/restore-db.sh to restore from a backup produced here, and
# infra/README.md for one-time S3 bucket / IAM setup.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

set -a
source .env.prod
set +a

BACKUP_DIR="${BACKUP_DIR:-$HOME/db-backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FILENAME="siavonga_run_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] Starting backup -> $BACKUP_DIR/$FILENAME"

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$FILENAME"

echo "[$(date -Iseconds)] Local dump complete ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"

if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
  if command -v aws >/dev/null 2>&1; then
    aws s3 cp "$BACKUP_DIR/$FILENAME" "s3://${BACKUP_S3_BUCKET}/${FILENAME}"
    echo "[$(date -Iseconds)] Uploaded to s3://${BACKUP_S3_BUCKET}/${FILENAME}"
  else
    echo "[$(date -Iseconds)] WARNING: BACKUP_S3_BUCKET is set but the aws CLI isn't installed — skipping upload" >&2
  fi
fi

# Local retention only — offsite retention in S3 is handled by a lifecycle
# rule on the bucket (see infra/README.md) rather than deleted from here.
find "$BACKUP_DIR" -name 'siavonga_run_*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete

echo "[$(date -Iseconds)] Backup done."
