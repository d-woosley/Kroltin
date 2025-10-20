#!/usr/bin/env bash

echo "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key='{{TAILSCALE_KEY}}'

# Check Installation Status
if tailscale status &> /dev/null; then
    echo "Tailscale installed and configured successfully."
else
    echo "Tailscale installation or configuration failed."
    exit 1
fi