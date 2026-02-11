#!/usr/bin/env bash
# Export PostgreSQL data from local Docker for migration to EC2.
# Run from intraday_predictor directory: ./scripts/export_db.sh
# Output: backups/predictions_YYYYMMDD_HHMMSS.sql

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUPS_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$BACKUPS_DIR/predictions_$TIMESTAMP.sql"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-predictor}"
POSTGRES_DB="${POSTGRES_DB:-predictions}"

mkdir -p "$BACKUPS_DIR"

echo "Exporting $POSTGRES_DB (user: $POSTGRES_USER) from local Docker..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
  pg_dump -U "$POSTGRES_USER" --no-owner --no-acl "$POSTGRES_DB" > "$OUTPUT_FILE"

echo "Exported to: $OUTPUT_FILE"
ls -lh "$OUTPUT_FILE"
