#!/usr/bin/env bash
# cloudflare-tunnel-setup.sh
#
# One-time setup to create a Cloudflare Tunnel for the home server backup.
# After this script, the tunnel token goes into CF_TUNNEL_TOKEN in your .env.
#
# Prerequisites:
#   - cloudflared CLI installed (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
#   - A Cloudflare account with a domain
#   - logged in via `cloudflared tunnel login`
#
# Usage:
#   bash cloudflare-tunnel-setup.sh
#
# What this does:
#   1. Creates a tunnel named "wai-home-server"
#   2. Routes your-domain.com/* to localhost:8080
#   3. Outputs the tunnel token — paste it into your .env as CF_TUNNEL_TOKEN
# ============================================================================

set -euo pipefail

TUNNEL_NAME="${TUNNEL_NAME:-wai-home-server}"
LOCAL_PORT="${LOCAL_PORT:-8080}"
DOMAIN="${DOMAIN:-}"

echo "==> Creating tunnel: $TUNNEL_NAME"
cloudflared tunnel create "$TUNNEL_NAME"

TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "==> Tunnel ID: $TUNNEL_ID"

echo "==> Creating DNS route..."
if [ -n "$DOMAIN" ]; then
  cloudflared tunnel route dns "$TUNNEL_ID" "$DOMAIN"
  echo "==> DNS route created: $DOMAIN → tunnel $TUNNEL_ID"
else
  echo "==> DOMAIN not set. Skipping DNS route."
  echo "    Run: cloudflared tunnel route dns $TUNNEL_ID your-domain.com"
fi

echo ""
echo "==> Getting tunnel token..."
TOKEN=$(cloudflared tunnel token "$TUNNEL_ID")
echo ""
echo "============================================================"
echo "  Tunnel token (keep secret):"
echo "  $TOKEN"
echo ""
echo "  Add to your .env file:"
echo "  CF_TUNNEL_TOKEN=$TOKEN"
echo "============================================================"
echo ""
echo "  To run the tunnel (via docker-compose or manually):"
echo "    cloudflared tunnel run $TUNNEL_ID"
echo ""
echo "  Or use docker-compose which runs it as a sidecar container."
echo "============================================================"
