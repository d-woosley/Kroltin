#!/usr/bin/env bash
# Script to change the current user's password to a randomly generated password
set -euo pipefail

# Change the user's password using the random password
echo "{{USERNAME}}:{{RANDOM_PASSWORD}}" | chpasswd

if [ $? -ne 0 ]; then
    exit 1
fi
