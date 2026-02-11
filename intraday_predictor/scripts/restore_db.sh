#!/usr/bin/env bash
# Restore PostgreSQL from a dump file (for EC2 or any target).
# Usage: ./scripts/restore_db.sh [path/to/dump.sql]
# If no path given, uses latest backup in backups/
# Requires: Docker running with db service, or psql available for remote Postgres.
#
# For EC2 with Docker: run from project dir, ensure .env has POSTGRES_* for target DB.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-predictor}"
POSTGRES_DB="${POSTGRES_DB:-predictions}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"

# Resolve dump file
if [ -n "$1" ]; then
  DUMP_FILE="$1"
else
  BACKUPS_DIR="$PROJECT_DIR/backups"
  if [ ! -d "$BACKUPS_DIR" ]; then
    echo "No backups directory and no dump file specified."
    exit 1
  fi
  DUMP_FILE=$(ls -t "$BACKUPS_DIR"/predictions_*.sql 2>/dev/null | head -1)
  if [ -z "$DUMP_FILE" ]; then
    echo "No dump file found in $BACKUPS_DIR"
    exit 1
  fi
  echo "Using latest dump: $DUMP_FILE"
fi

if [ ! -f "$DUMP_FILE" ]; then
  echo "Dump file not found: $DUMP_FILE"
  exit 1
fi

# Restore via Docker (when Postgres runs in Docker on same machine)
if [ "$POSTGRES_HOST" = "localhost" ] || [ "$POSTGRES_HOST" = "127.0.0.1" ]; then
  echo "Restoring to local Docker..."
  cat "$DUMP_FILE" | docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
else
  # Remote (e.g. EC2): use psql directly (must be installed and PGPASSWORD set)
  echo "Restoring to $POSTGRES_HOST..."
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$DUMP_FILE"
fi

echo "Restore complete."
