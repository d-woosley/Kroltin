#!/usr/bin/env bash
set -euo pipefail

echo "[test] ==========================================" >&2
echo "[test] Template Variables" >&2
echo "[test] ==========================================" >&2
echo "[test] USERNAME='{{USERNAME}}'" >&2
echo "[test] HOSTNAME='{{HOSTNAME}}'" >&2
echo "[test] TAILSCALE_KEY='{{TAILSCALE_KEY}}'" >&2
echo "[test] ==========================================" >&2
