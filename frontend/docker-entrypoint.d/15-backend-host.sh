#!/bin/sh
# Derives BACKEND_HOST from BACKEND_URL so the nginx template can set the
# Host header correctly when proxying /api to the backend service.
#
# Runs before the image's 20-envsubst-on-templates.sh (alphabetical order),
# which means ${BACKEND_HOST} is a *defined* env var by the time the template
# is rendered — without this, envsubst leaves ${BACKEND_HOST} literal and
# nginx refuses to start (unknown "BACKEND_HOST" variable).
#
# BACKEND_HOST is only derived when not explicitly provided. Override it
# explicitly when the backend's public hostname differs from its URL host
# (e.g. when proxying through a tunnel or alias domain).
set -e

if [ -z "${BACKEND_HOST:-}" ]; then
  BACKEND_HOST="$(printf '%s' "${BACKEND_URL:-http://backend:8080}" | sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##; s#[:/].*$##')"
  # Safety net: never let the template render an empty Host header.
  [ -n "$BACKEND_HOST" ] || BACKEND_HOST="backend"
  export BACKEND_HOST
fi
