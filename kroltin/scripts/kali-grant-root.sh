#!/usr/bin/env bash

apt install kali-grant-root -y
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure kali-grant-root
