#!/bin/sh
set -e

# Executive seat configuration check.
#
# Previously this refused to boot when no exec seat email was configured
# (fail-closed). That turned a config gap into a silent healthcheck death:
# the container exited before uvicorn bound its port, Railway reported only
# "service unavailable", and the only way to diagnose was reading deploy
# logs — work dumped on the site owner.
#
# Now we boot ALWAYS and close the actual risk instead: with no seat email,
# the register endpoint does NOT award executive_admin to the first
# registrant (see routers/auth.py — bootstrap grant requires a configured
# seat). The site stays publicly reachable either way; adding the variable
# later takes effect on the next deploy.
if [ -z "${EXEC_ADMIN_EMAIL}" ] && [ -z "${BACKUP_EXEC_ADMIN_EMAIL}" ] && [ -z "${NAM_EXEC_EMAIL}" ]; then
  echo "WARNING: No executive admin email configured (EXEC_ADMIN_EMAIL / BACKUP_EXEC_ADMIN_EMAIL / NAM_EXEC_EMAIL)."
  echo "WARNING: Booting anyway. First-registration executive bootstrap is LOCKED until a seat email is set."
fi

BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
BACKEND_URL="${BACKEND_URL%/}"
BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|^https\?://||' | cut -d'/' -f1)
export BACKEND_URL
export BACKEND_HOST
TARGET_PORT=${PORT:-8080}
exec uvicorn backend.server:app --host 0.0.0.0 --port "$TARGET_PORT"
