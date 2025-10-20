#!/usr/bin/env bash

apt install kali-grant-root -y
printf 'kali-grant-root kali-grant-root/enable boolean true\n' | debconf-set-selections
DEBIAN_FRONTEND=noninteractive dpkg-reconfigure -f noninteractive -p low kali-grant-root
