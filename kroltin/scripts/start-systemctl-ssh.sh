#!/usr/bin/env bash
set -euo pipefail

systemctl enable ssh
systemctl start ssh
