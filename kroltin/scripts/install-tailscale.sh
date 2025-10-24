#!/usr/bin/env bash
set -euo pipefail

echo "Installing Tailscale..."
apt install curl -y
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key='{{TAILSCALE_KEY}}'
