#!/usr/bin/env bash
set -euo pipefail

echo "[install-tailscale] Installing curl prerequisite" >&2
apt install curl -y
echo "[install-tailscale] Running Tailscale installer" >&2
curl -fsSL https://tailscale.com/install.sh | sh
echo "[install-tailscale] Bringing up Tailscale with auth key" >&2
tailscale up --auth-key='{{TAILSCALE_KEY}}'
echo "[install-tailscale] Tailscale setup complete" >&2
