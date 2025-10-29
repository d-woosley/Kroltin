#!/usr/bin/env bash
set -euo pipefail

echo "[kali-grant-root] Installing kali-grant-root package" >&2
apt install kali-grant-root -y
printf 'kali-grant-root kali-grant-root/enable boolean true\n' | debconf-set-selections
echo "[kali-grant-root] Reconfiguring package to enable feature" >&2
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure -f noninteractive -p low kali-grant-root

# Add Self to kali-trusted
echo "[kali-grant-root] Adding user {{USERNAME}} to kali-trusted group" >&2
usermod -aG kali-trusted {{USERNAME}}
echo "[kali-grant-root] Completed root grant adjustments" >&2
