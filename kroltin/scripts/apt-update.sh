#!/usr/bin/env bash
set -euo pipefail

apt-get update -y
apt-get dist-upgrade -y
apt-get autoremove -y
