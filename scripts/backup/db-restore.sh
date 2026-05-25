#!/usr/bin/env bash
# WAI Institute — MongoDB restore script
# Usage: ./scripts/backup/db-restore.sh <backup_file.gz>

set -euo pipefail

MONGO_URL="${MONGO_URL:-mongodb://localhost:27017/wai}"
BACKUP_FILE="${1:-}"

if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup_file.gz>"
  echo "Available backups:"
  ls -lh ./backups/ 2>/dev/null || echo "  (no backups found)"
  exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Error: file not found: ${BACKUP_FILE}"
  exit 1
fi

echo "→ Restoring ${BACKUP_FILE} → ${MONGO_URL}"
echo "⚠ WARNING: This will OVERWRITE the current database!"
read -rp "Type 'yes' to continue: " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

mongorestore --uri="${MONGO_URL}" --archive="${BACKUP_FILE}" --gzip --drop
echo "✓ Restore complete."
