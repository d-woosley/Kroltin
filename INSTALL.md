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

   **Using PowerShell (as Administrator):**
   ```powershell
   # For current user only
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\packer", "User")
   
   # OR for all users (requires admin)
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\packer", "Machine")
   ```
   
   **Using GUI:**
   - Search for "Environment Variables" in Windows Start menu
   - Click "Edit the system environment variables"
   - Click "Environment Variables..." button
   - Under "System variables" (or "User variables"), find and select "Path"
   - Click "Edit..."
   - Click "New"
   - Add the directory containing `packer.exe` (e.g., `C:\packer\`)
   - Click "OK" on all dialogs
   
   **Close and reopen your terminal** for changes to take effect.
   
Verify installation:
```cmd
packer version
```

> ⚠️ **Note:** If `packer version` doesn't work after manual installation, you may need to manually add Packer to your PATH using one of the methods above.

### 4. Install a Virtualization Platform

**Option A: VMware Workstation**

1. Download and install [VMware Workstation Pro](https://www.vmware.com/products/workstation-pro.html)
2. The CLI tools (`vmrun`, `ovftool`) should be automatically added to PATH during installation
3. Verify installation:
   ```cmd
   vmrun
   ovftool
   ```

> ⚠️ **Note:** If `vmrun` or `ovftool` commands are not recognized:
> 
> **Using PowerShell (as Administrator):**
> ```powershell
> # Add VMware paths (adjust if your installation path differs)
> $vmwarePath = "C:\Program Files (x86)\VMware\VMware Workstation"
> $ovfToolPath = "C:\Program Files (x86)\VMware\VMware Workstation\OVFTool"
> 
> # For current user
> [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$vmwarePath;$ovfToolPath", "User")
> 
> # OR for all users (requires admin)
> [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$vmwarePath;$ovfToolPath", "Machine")
> ```
> 
> **Using GUI:**
> 1. Locate your VMware installation directory (typically `C:\Program Files (x86)\VMware\VMware Workstation\`)
> 2. Add these paths to your system PATH using the Environment Variables steps from section 3:
>    - `C:\Program Files (x86)\VMware\VMware Workstation\`
>    - `C:\Program Files (x86)\VMware\VMware Workstation\OVFTool\`
> 3. Close and reopen your terminal

**Option B: VirtualBox**

1. Download and install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
2. The installer should automatically add `VBoxManage` to PATH
3. Verify installation:
   ```cmd
   VBoxManage --version
   ```

> ⚠️ **Note:** If `VBoxManage` command is not recognized:
> 
> **Using PowerShell (as Administrator):**
> ```powershell
> # Add VirtualBox path (adjust if your installation path differs)
> $vboxPath = "C:\Program Files\Oracle\VirtualBox"
> 
> # For current user
> [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$vboxPath", "User")
> 
> # OR for all users (requires admin)
> [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$vboxPath", "Machine")
> ```
> 
> **Using GUI:**
> 1. Locate your VirtualBox installation directory (typically `C:\Program Files\Oracle\VirtualBox\`)
> 2. Add this path to your system PATH using the Environment Variables steps from section 3:
>    - `C:\Program Files\Oracle\VirtualBox\`
> 3. Close and reopen your terminal

### 5. Open Preseed HTTP Firewall Port
Windows golden image builds will need to serve the preseed file over an HTTP server on port 8804. Therefore, you will have to allow packer to open this port on the firewall using the following command (Run as Administrator).

```PowerShell
New-NetFirewallRule -DisplayName "Packer HTTP Server" -Direction Inbound -Program (Get-Command packer).Path -Protocol TCP -LocalPort 8804 -Action Allow -Profile Private
```

### 6. Install Kroltin

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
