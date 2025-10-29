#!/usr/bin/env bash
set -euo pipefail

echo "[apt-update] Running apt-get update" >&2
apt-get update -y
echo "[apt-update] Running dist-upgrade" >&2
apt-get dist-upgrade -y
echo "[apt-update] Running autoremove" >&2
apt-get autoremove -y
echo "[apt-update] Completed apt maintenance" >&2
