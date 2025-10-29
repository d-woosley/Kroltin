#!/usr/bin/env bash
# Script to change the current user's password to a randomly generated password
set -euo pipefail

# Change the user's password using the random password
echo "[randomize-password] Updating password for {{USERNAME}}" >&2
echo "{{USERNAME}}:{{RANDOM_PASSWORD}}" | chpasswd

if [ $? -ne 0 ]; then
    echo "[randomize-password][ERROR] Password change failed" >&2
    exit 1
fi
echo "[randomize-password] Password successfully changed" >&2
