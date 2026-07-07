#!/usr/bin/env bash
# ─── System Dependencies Setup ──────────────────────────────────────────────
# Installe les paquets système requis par WireGuard UI (wg-quick, iptables).
set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧  Installing system dependencies                  "
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  wireguard-tools \
  iptables

echo "  ✅  wireguard-tools & iptables installed"
