#!/bin/bash

# Must be run as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root. Use 'sudo' to run it."
  exit 1
fi

# Install Packer
wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt update && apt install packer
command -v packer >/dev/null 2>&1 || { echo "Error: packer is not installed." >&2; exit 1; }

# Install VMWare Workstation Player
apt install build-essential linux-headers-$(uname -r) -y
# NOT COMPLETED: The installation of VMWare Workstation Player requires manual steps.
echo "Please download and install VMWare Workstation Player manually."

# Install VirtualBox
curl -fsSL https://www.virtualbox.org/download/oracle_vbox_2016.asc| gpg --dearmor -o /etc/apt/trusted.gpg.d/vbox.gpg
curl -fsSL https://www.virtualbox.org/download/oracle_vbox.asc| gpg --dearmor -o /etc/apt/trusted.gpg.d/oracle_vbox.gpg
echo "deb [arch=amd64] http://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" | tee /etc/apt/sources.list.d/virtualbox.list
sudo apt install linux-headers-$(uname -r) dkms -y
apt install virtualbox -y
command -v virtualbox >/dev/null 2>&1 || { echo "Error: VirtualBox is not installed." >&2; exit 1; }


