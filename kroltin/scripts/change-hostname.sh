#!/usr/bin/env bash
# Changes the system hostname to the value provided in the HOSTNAME variable
set -euo pipefail

NEW_HOSTNAME="{{HOSTNAME}}"

# Update /etc/hostname
echo "${NEW_HOSTNAME}" | sudo tee /etc/hostname

# Update /etc/hosts - replace old hostname with new one
OLD_HOSTNAME=$(hostname)
sudo sed -i "s/${OLD_HOSTNAME}/${NEW_HOSTNAME}/g" /etc/hosts

# Also ensure localhost entries are correct
if ! grep -q "127.0.1.1.*${NEW_HOSTNAME}" /etc/hosts; then
    echo "127.0.1.1    ${NEW_HOSTNAME}" | sudo tee -a /etc/hosts
fi

# Set the hostname immediately (without reboot)
sudo hostnamectl set-hostname "${NEW_HOSTNAME}"

# Verify the change
echo "============================================"
echo "Hostname changed successfully!"
echo "Old hostname: ${OLD_HOSTNAME}"
echo "New hostname: $(hostname)"
echo "============================================"
