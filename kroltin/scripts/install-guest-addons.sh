#!/usr/bin/env bash
# Install virtualization-specific guest additions and apply optional Xorg
# configuration to mitigate invisible cursor issues. Safe to run multiple times.
# This script intentionally focuses only on guest additions and display tweaks;
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Detect virtualization type
virt_type="$(systemd-detect-virt || true)"
[ -z "$virt_type" ] && virt_type="unknown"
echo "[install-guest-addons] Detected virtualization: $virt_type" >&2

# Package install helper (idempotent)
install_pkgs() {
  local pkgs=("$@")
  local to_install=()
  for p in "${pkgs[@]}"; do
    if dpkg -s "$p" >/dev/null 2>&1; then
      echo "[install-guest-addons] Package already installed: $p" >&2
    else
      to_install+=("$p")
    fi
  done
  if [ ${#to_install[@]} -gt 0 ]; then
    echo "[install-guest-addons] Installing packages: ${to_install[*]}" >&2
    apt-get update -y >/dev/null || true
    apt-get install -y --no-install-recommends "${to_install[@]}"
  else
    echo "[install-guest-addons] All requested packages already installed" >&2
  fi
}

case "$virt_type" in
  vmware)
    install_pkgs open-vm-tools-desktop
    x_driver="vmware"
    ;;
  oracle|virtualbox)
    # Try both guest additions variants; ignore failure of one.
    install_pkgs virtualbox-guest-utils virtualbox-guest-x11 || true
    x_driver="vboxvideo"
    ;;
  kvm|qemu)
    install_pkgs spice-vdagent
    # Prefer qxl driver if module present; else modesetting.
    if lsmod | grep -q qxl; then
      x_driver="qxl"
    else
      x_driver="modesetting"
    fi
    ;;
  microsoft|hyperv)
    install_pkgs linux-cloud-tools-virtual linux-tools-virtual || true
    x_driver="modesetting"
    ;;
  xen)
    install_pkgs xen-tools || true
    x_driver="modesetting"
    ;;
  *)
    echo "[install-guest-addons][WARN] Unrecognized virtualization type; proceeding with generic settings" >&2
    x_driver="modesetting"
    ;;
 esac

echo "[install-guest-addons] Guest additions installation complete" >&2
