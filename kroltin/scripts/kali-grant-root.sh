#!/usr/bin/env bash
set -euo pipefail

apt install kali-grant-root -y
printf 'kali-grant-root kali-grant-root/enable boolean true\n' | debconf-set-selections
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure -f noninteractive -p low kali-grant-root

# Add Self to kali-trusted
usermod -aG kali-trusted "$(whoami)"
