#!/usr/bin/env bash
# Changes the system hostname to the value provided in the HOSTNAME variable
set -euo pipefail

NEW_HOSTNAME="{{HOSTNAME}}"

echo "[change-hostname] Updating /etc/hostname to '${NEW_HOSTNAME}'" >&2
echo "${NEW_HOSTNAME}" | sudo tee /etc/hostname >/dev/null

# Update /etc/hosts - replace old hostname with new one
OLD_HOSTNAME=$(hostname)
echo "[change-hostname] Rewriting /etc/hosts entries from '${OLD_HOSTNAME}' to '${NEW_HOSTNAME}'" >&2
sudo sed -i "s/${OLD_HOSTNAME}/${NEW_HOSTNAME}/g" /etc/hosts

# Also ensure localhost entries are correct
if ! grep -q "127.0.1.1.*${NEW_HOSTNAME}" /etc/hosts; then
    echo "[change-hostname] Adding 127.0.1.1 mapping for ${NEW_HOSTNAME}" >&2
    echo "127.0.1.1    ${NEW_HOSTNAME}" | sudo tee -a /etc/hosts >/dev/null
fi

# Set the hostname immediately (without reboot)
echo "[change-hostname] Setting runtime hostname" >&2
sudo hostnamectl set-hostname "${NEW_HOSTNAME}"

# Verify the change
echo "[change-hostname] Hostname changed successfully (old='${OLD_HOSTNAME}', new='$(hostname)')" >&2
