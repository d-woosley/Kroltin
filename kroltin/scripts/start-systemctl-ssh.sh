#!/usr/bin/env bash
set -euo pipefail

echo "[start-systemctl-ssh] Enabling ssh service" >&2
systemctl enable ssh
echo "[start-systemctl-ssh] Starting ssh service" >&2
systemctl start ssh
echo "[start-systemctl-ssh] ssh service enabled and started" >&2
