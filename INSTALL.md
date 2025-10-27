# Installation Guide

This guide provides detailed installation instructions for Kroltin on Windows, Linux, and WSL.

## Prerequisites

Before using Kroltin, you need:
- **Python 3.8 or later**
- **HashiCorp Packer** (required)
- **At least one virtualization platform**: VMware Workstation/Fusion **OR** VirtualBox

> ℹ️ You only need to install **one** of the virtualization platforms (VMware or VirtualBox), not both.

---

## Windows Installation

### 1. Install Python

Download and install Python 3.8 or later from [python.org](https://www.python.org/downloads/). Make sure to check "Add Python to PATH" during installation.

Verify installation:
```cmd
python --version
```

### 2. Install pipx

```cmd
python -m pip install --user pipx
python -m pipx ensurepath
```

Close and reopen your terminal after running `ensurepath`.

### 3. Install HashiCorp Packer

**Option A: Using Chocolatey (recommended)**
```cmd
choco install packer
```

**Option B: Manual Installation**
1. Download the Windows binary from [packer.io/downloads](https://www.packer.io/downloads)
2. Extract the executable to a directory (e.g., `C:\packer\`)
3. Add the directory to your PATH:
   - Search for "Environment Variables" in Windows
   - Edit "Path" under System Variables
   - Add the directory containing `packer.exe`
   
Verify installation:
```cmd
packer version
```

### 4. Install a Virtualization Platform

**Option A: VMware Workstation**

1. Download and install [VMware Workstation Pro](https://www.vmware.com/products/workstation-pro.html)
2. The CLI tools (`vmrun`, `ovftool`) are automatically added to PATH during installation
3. Verify installation:
   ```cmd
   vmrun
   ovftool
   ```

**Option B: VirtualBox**

1. Download and install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
2. The installer automatically adds `VBoxManage` to PATH
3. Verify installation:
   ```cmd
   VBoxManage --version
   ```

### 5. Install Kroltin

```cmd
pipx install git+https://github.com/d-woosley/Kroltin.git
```

---

## Linux Installation

### 1. Install Python and pipx

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install python3 python3-pip pipx
pipx ensurepath
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip pipx
pipx ensurepath
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip python-pipx
pipx ensurepath
```

Reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### 2. Install HashiCorp Packer

**Option A: Using Package Manager (Debian/Ubuntu)**
```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install packer
```

**Option B: Manual Installation**
```bash
wget https://releases.hashicorp.com/packer/1.10.0/packer_1.10.0_linux_amd64.zip
unzip packer_1.10.0_linux_amd64.zip
sudo mv packer /usr/local/bin/
sudo chmod +x /usr/local/bin/packer
```

Verify installation:
```bash
packer version
```

### 3. Install a Virtualization Platform

**Option A: VMware Workstation**

1. Download VMware Workstation from [vmware.com](https://www.vmware.com/products/workstation-pro.html)
2. Install:
   ```bash
   sudo chmod +x VMware-Workstation-*.bundle
   sudo ./VMware-Workstation-*.bundle
   ```
3. Add VMware tools to PATH by adding to `~/.bashrc` or `~/.zshrc`:
   ```bash
   export PATH=$PATH:/usr/bin/vmware
   export PATH=$PATH:/usr/lib/vmware/bin
   export PATH=$PATH:/usr/lib/vmware-ovftool
   ```
4. Reload shell and verify:
   ```bash
   source ~/.bashrc
   vmrun
   ovftool
   ```

**Troubleshooting VMware on Debian:**
If VMware modules fail to load:
```bash
sudo vmware-modconfig --console --install-all
```

**Option B: VirtualBox**

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install virtualbox

# Fedora
sudo dnf install VirtualBox

# Arch Linux
sudo pacman -S virtualbox
```

Verify installation:
```bash
VBoxManage --version
```

### 4. Install Kroltin

```bash
pipx install git+https://github.com/d-woosley/Kroltin.git
```

---

## WSL (Windows Subsystem for Linux) Installation

### 1. Set Up WSL

If you haven't already installed WSL:
```cmd
wsl --install
```

Launch your WSL distribution (Ubuntu recommended).

### 2. Install Python and pipx

```bash
sudo apt update
sudo apt install python3 python3-pip pipx
pipx ensurepath
source ~/.bashrc
```

### 3. Install HashiCorp Packer

```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install packer
```

Verify installation:
```bash
packer version
```

### 4. Install a Virtualization Platform

**Important:** Virtualization platforms must be installed on the **Windows host**, not inside WSL.

**Option A: VMware Workstation (on Windows host)**

1. Install VMware Workstation on Windows as described in the Windows section
2. Access VMware tools from WSL by adding Windows paths to your WSL PATH in `~/.bashrc`:
   ```bash
   export PATH=$PATH:"/mnt/c/Program Files (x86)/VMware/VMware Workstation"
   export PATH=$PATH:"/mnt/c/Program Files/VMware/VMware Workstation"
   ```
3. Create aliases for the Windows executables so Kroltin can call them without the `.exe` extension. Add to `~/.bashrc`:
   ```bash
   alias vmrun='vmrun.exe'
   alias ovftool='ovftool.exe'
   ```
4. Reload shell and verify:
   ```bash
   source ~/.bashrc
   vmrun
   ovftool
   ```

**Option B: VirtualBox (on Windows host)**

1. Install VirtualBox on Windows as described in the Windows section
2. Access VirtualBox tools from WSL by adding Windows paths to your WSL PATH in `~/.bashrc`:
   ```bash
   export PATH=$PATH:"/mnt/c/Program Files/Oracle/VirtualBox"
   ```
3. Create an alias for the Windows executable so Kroltin can call it without the `.exe` extension. Add to `~/.bashrc`:
   ```bash
   alias vboxmanage='VBoxManage.exe'
   ```
4. Reload shell and verify:
   ```bash
   source ~/.bashrc
   vboxmanage --version
   ```

### 5. Install Kroltin

```bash
pipx install git+https://github.com/d-woosley/Kroltin.git
```

---

## Verify Installation

After completing the installation for your platform, verify everything is working:

```bash
kroltin --help
packer version
```

And verify your chosen virtualization platform:

```bash
# For VMware
vmrun

# For VirtualBox
VBoxManage --version
```

---

## Quick Install (Advanced Users)

If you already have all prerequisites installed, you can quickly install Kroltin:

```bash
pipx install git+https://github.com/d-woosley/Kroltin.git
```

**Prerequisites:**
- Python 3.8 or later
- [HashiCorp Packer](https://www.packer.io/downloads)
- VMware Workstation/Fusion or VirtualBox CLI tools in PATH

---

## Next Steps

Once installation is complete, check out the [main README](README.md) for:
- Usage examples
- Template system documentation
- Command reference
- Troubleshooting tips
