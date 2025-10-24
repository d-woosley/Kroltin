#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get install -y kali-desktop-gnome gdm3 xorg open-vm-tools-desktop dbus-x11
echo "gdm3 shared/default-x-display-manager select gdm3" | debconf-set-selections
dpkg-reconfigure -f noninteractive gdm3
systemctl set-default graphical.target
