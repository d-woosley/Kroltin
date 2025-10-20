#!/usr/bin/env bash
set -eux
apt-get update -y
apt-get dist-upgrade -y
apt-get autoremove -y
