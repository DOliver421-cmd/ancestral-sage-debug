#!/bin/sh
set -e

# Fail-closed exec configuration: refuse to boot when NO executive seat email
# is configured. Without an exec seat the startup seed creates none, and on a
# fresh database the first registrant becomes executive_admin (god-mode).
# Every exec email must be explicitly set in Railway Variables — there are no
# hardcoded fallbacks in source.
if [ -z "${EXEC_ADMIN_EMAIL}" ] && [ -z "${BACKUP_EXEC_ADMIN_EMAIL}" ] && [ -z "${NAM_EXEC_EMAIL}" ]; then
  echo "FATAL: No executive admin email configured. Set EXEC_ADMIN_EMAIL, BACKUP_EXEC_ADMIN_EMAIL, or NAM_EXEC_EMAIL in Railway Variables before deploying." >&2
  exit 1
fi

BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
BACKEND_URL="${BACKEND_URL%/}"
BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|^https\?://||' | cut -d'/' -f1)
export BACKEND_URL
export BACKEND_HOST
TARGET_PORT=${PORT:-8080}
exec uvicorn backend.server:app --host 0.0.0.0 --port "$TARGET_PORT"
