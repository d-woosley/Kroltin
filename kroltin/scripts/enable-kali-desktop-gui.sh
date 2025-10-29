#!/usr/bin/env bash
# This script enables the Kali GNOME desktop GUI.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "[enable-kali-desktop-gui] Installing core desktop packages" >&2
apt-get install -y --no-install-recommends \
	kali-desktop-gnome gdm3 xorg dbus-x11 \
	adwaita-icon-theme dmz-cursor-theme \
	xserver-xorg-input-all

# Create /etc/X11/xorg.conf if not present to address invisible cursor issues.
if [ ! -f /etc/X11/xorg.conf ]; then
	case "$virt_type" in
		vmware) x_driver="vmware" ;;
		oracle|virtualbox) x_driver="vboxvideo" ;;
		kvm|qemu) x_driver="modesetting" ;;
		*) x_driver="modesetting" ;;
	esac
	cat >/etc/X11/xorg.conf <<EOF
Section "ServerLayout"
	Identifier "X.org Configured"
	InputDevice "Mouse0" "CorePointer"
	InputDevice "Keyboard0" "CoreKeyboard"
EndSection
Section "InputDevice"
	Identifier "Keyboard0"
	Driver "kbd"
EndSection
Section "InputDevice"
	Identifier "Mouse0"
	Driver "mouse"
	Option "Protocol" "auto"
	Option "Device" "/dev/input/mice"
	Option "ZAxisMapping" "4 5 6 7"
EndSection
Section "Device"
	Option "HWcursor" "off"
	Identifier "Card0"
	Driver "${x_driver}"
EndSection
EOF
	echo "[enable-kali-desktop-gui] Created /etc/X11/xorg.conf with driver '${x_driver}' and HWcursor disabled" >&2
else
	echo "[enable-kali-desktop-gui] Existing /etc/X11/xorg.conf detected; leaving unchanged" >&2
fi

# Ensure gdm3 is the display manager.
echo "gdm3 shared/default-x-display-manager select gdm3" | debconf-set-selections
dpkg-reconfigure -f noninteractive gdm3 || true
systemctl set-default graphical.target

echo "[enable-kali-desktop-gui] Desktop environment provisioning complete" >&2
