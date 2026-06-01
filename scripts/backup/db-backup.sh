#!/usr/bin/env bash
# WAI Institute — MongoDB backup script
# Usage: ./scripts/backup/db-backup.sh [output_dir]
# Default output: ./backups/wai-YYYY-MM-DD-HHMMSS.gz

set -euo pipefail

MONGO_URL="${MONGO_URL:-mongodb://localhost:27017/wai}"
OUTPUT_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
OUTPUT="${OUTPUT_DIR}/wai-${TIMESTAMP}.gz"

mkdir -p "${OUTPUT_DIR}"

echo "→ Backing up ${MONGO_URL} → ${OUTPUT}"
mongodump --uri="${MONGO_URL}" --archive="${OUTPUT}" --gzip
echo "✓ Backup complete: $(du -h "${OUTPUT}" | cut -f1)"

# Keep only last 30 days
find "${OUTPUT_DIR}" -name "wai-*.gz" -mtime +30 -delete
