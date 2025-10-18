# Kroltin

A CLI tool for automating the creation and configuration of virtual machine environments using HashiCorp Packer.

## Overview

Kroltin automates VM image creation from ISO files and applies configuration to existing VM images. It currently supports VMware and VirtualBox (requires their CLI tools in PATH). Hyper-V support is planned but not yet implemented.

The tool handles:
- Building golden images from ISO files
- Applying additional configuration to existing VMs
- Template variable substitution in preseed files and bash scripts
- Script and resource management
- Automatic cleanup of temporary build files

## Installation

Install directly from GitHub using pipx:

```bash
pipx install git+https://github.com/d-woosley/Kroltin.git
```

**Prerequisites:**
- Python 3.8 or later
- [HashiCorp Packer](https://www.packer.io/downloads)
- VMware Workstation/Fusion or VirtualBox CLI tools in PATH

## Usage

### Building a Golden Image

It's recommended to build a golden image first. Golden images can be reused for faster configuration runs later.

```bash
kroltin golden \
  --vm-type vmware \
  --vm-name kali-base-2024 \
  --packer-template build.pkr.hcl \
  --iso https://cdimage.kali.org/kali-2024.3/kali-linux-2024.3-installer-amd64.iso \
  --iso-checksum "sha256:checksum_here" \
  --preseed-file kali-linux_2503.cfg \
  --cpus 4 \
  --memory 8192 \
  --disk-size 81920 \
  --scripts software.sh cleanup.sh \
  --ssh-username kali
```

If no `--ssh-password` is provided, you will be prompted to enter one. **Do not supply passwords inline in the command.**

> ℹ️ Password changes during configuration builds are not yet supported.

### Configuring an Existing VM

Configuration builds are final products and cannot be saved back to the kroltin installation folder. They are exported to a specified path.

```bash
kroltin configure \
  --vm-type vmware \
  --vm-name configured-kali \
  --vm-file kali-base-2024 \
  --packer-template configure.pkr.hcl \
  --scripts custom-setup.sh \
  --export-path ./configured-vm \
  --ssh-username kali
```

### Building and Exporting a Golden Image Only

You can build a golden image without further configuration and export it for use elsewhere:

```bash
kroltin golden \
  --vm-type virtualbox \
  --vm-name kali-export \
  --packer-template build.pkr.hcl \
  --iso /path/to/kali.iso \
  --iso-checksum "sha256:abc123..." \
  --preseed-file kali-linux_2503.cfg \
  --ssh-username kali
```

After the build completes, export the golden image:

```bash
kroltin settings --export-golden-image kali-export --export-path ./export/
```

## Template Variables

Kroltin supports dynamic variable substitution in preseed files and bash scripts using `{{VARIABLE}}` syntax.

### Available Variables

| Variable | CLI Argument | Description |
|----------|--------------|-------------|
| `{{USERNAME}}` | `--ssh-username` | SSH username (default: `kroltin`) |
| `{{PASSWORD_CRYPT}}` | `--ssh-password` | SHA-512 crypt hash of the SSH password |
| `{{HOSTNAME}}` | `--hostname` | Hostname (default: uses `--vm-name`) |
| `{{TAILSCALE_KEY}}` | `--tailscale-key` | Tailscale authentication key for automatic network setup |

### Usage in Preseed Files

```cfg
d-i passwd/user-fullname string {{USERNAME}}
d-i passwd/username string {{USERNAME}}
d-i passwd/user-password-crypted password {{PASSWORD_CRYPT}}
d-i netcfg/get_hostname string {{HOSTNAME}}
```

### Usage in Bash Scripts

```bash
#!/bin/bash
echo "Setting up user: {{USERNAME}}"
echo "Hostname: {{HOSTNAME}}"
useradd -m -s /bin/bash {{USERNAME}}
echo "{{USERNAME}}:{{PASSWORD_CRYPT}}" | chpasswd -e

# Install and configure Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --authkey={{TAILSCALE_KEY}} --hostname={{HOSTNAME}}
```

Variables are automatically detected and filled before script execution. If a script contains variables not provided via CLI, you will be prompted to proceed.

## Customization

You can create custom virtual machine by writing your own bash scripts. Execute permissions are not required since scripts run inside the VM during provisioning.

**VM Build Formats:**
- VMware builds produce a directory containing a `.vmx` file and supporting files
- VirtualBox builds produce a single `.ova` file

**Configuration Export Formats:**

Configuration builds support multiple export formats via `--export-file-type`:
- `ova` (default): Open Virtual Appliance format
- `ovf`: Open Virtualization Format
- `vmx`: VMware native format (VMware only)

**Golden Image Import Requirements:**

When importing golden images, VMware require `.vmx` files and VirtualBox requires `.ova` files.

## Settings Management

List all available resources:

```bash
kroltin -ls
# or
kroltin settings -ls
# or
kroltin settings --list-all
```

> ℹ️ These commands are equivalent.

Add custom resources:

```bash
kroltin settings --add-script /path/to/script.sh
kroltin settings --add-packer-template /path/to/template.pkr.hcl
kroltin settings --add-preseed-file /path/to/preseed.cfg
```

Remove resources:

```bash
kroltin settings --rm-script script.sh
kroltin settings --rm-golden-image old-vm
```

Import or export golden images:

```bash
kroltin settings --import-golden-image /path/to/vm
kroltin settings --export-golden-image vm-name --export-path ./backups/
```

## Debugging

Enable debug mode for detailed logging. Note that debug output is very verbose:

```bash
kroltin --debug --log golden ...
```

> ℹ️ Logs are written to `kroltin.log` by default.

## Command Reference

### Global Options

| Option | Description |
|--------|-------------|
| `-d, --debug` | Enable verbose debug output |
| `-l, --log` | Enable logging to file |
| `-lf, --log-file <PATH>` | Log file path (default: `kroltin.log`) |
| `-ls` | List all resources |

### Golden Command

```bash
kroltin golden [OPTIONS]
```

**Required:**
- `--vm-type <TYPE>`: Platform type (`vmware`, `virtualbox`, `all`)
- `--packer-template <PATH>`: Packer template file
- `--iso <URL/PATH>`: ISO file(s) (can specify multiple)
- `--iso-checksum <HASH>`: ISO checksum (`sha256:...`)
- `--preseed-file <FILE>`: Preseed/kickstart file

**VM Configuration:**
- `--vm-name <NAME>`: VM name (default: `kroltin-TIMESTAMP`)
- `--cpus <NUM>`: CPU count (default: 2)
- `--memory <MB>`: Memory in MB (default: 4096)
- `--disk-size <MB>`: Disk size in MB (default: 81920)
- `--guest-os-type <TYPE>`: Guest OS type (default: `debian_64`)
- `--vmware-version <NUM>`: VMware hardware version (default: 16)

**Template Variables:**
- `--ssh-username <USER>`: SSH username (default: `kroltin`)
- `--ssh-password <PASS>`: SSH password (prompted if omitted)
- `-rp, --random-password`: Generate random 30-character password
- `--hostname <NAME>`: Hostname (default: uses `--vm-name`)
- `--tailscale-key <KEY>`: Tailscale authentication key for automatic network setup

**Scripts:**
- `--scripts <SCRIPT>...`: Scripts to run (space-separated)
- `--no-headless`: Show VM GUI during build

### Configure Command

```bash
kroltin configure [OPTIONS]
```

**Required:**
- `--vm-type <TYPE>`: Platform type (`vmware`, `virtualbox`, `all`)
- `--packer-template <PATH>`: Packer template file
- `--vm-file <PATH>`: Source VM file or name

**Configuration:**
- `--vm-name <NAME>`: Output VM name (default: `kroltin-TIMESTAMP`)
- `--export-path <PATH>`: Export directory (default: `kroltin_configured_vm_TIMESTAMP`)
- `--export-file-type <TYPE>`: Export format (`ova`, `ovf`, `vmx`; default: `ova`)

**Template Variables:**
- `--ssh-username <USER>`: SSH username (default: `kroltin`)
- `--ssh-password <PASS>`: SSH password (prompted if omitted)
- `-rp, --random-password`: Generate random 30-character password
- `--hostname <NAME>`: Hostname (default: uses `--vm-name`)
- `--tailscale-key <KEY>`: Tailscale authentication key for automatic network setup

**Scripts:**
- `--scripts <SCRIPT>...`: Scripts to run (space-separated)
- `--no-headless`: Show VM GUI during configuration

## Recommendations

- Build golden images once and reuse them for faster configuration runs
- Use the `--scripts` flag to customize VMs with your own provisioning scripts
- Keep ISO files local when possible for faster builds
- Use `--random-password` for temporary VMs; store passwords securely for production use

## Troubleshooting

### VMware on Debian

If VMware Workstation module installation fails on Debian:

```bash
sudo vmware-modconfig --console --install-all
```

### Packer Validation

Verify your Packer templates before running builds:

```bash
packer validate template.pkr.hcl
```

## Future Plans

The following features are planned:

- **Hyper-V support**: Full integration with Hyper-V virtualization
- **Cloud provider support**: AWS, Azure, and GCP integration
- **Windows VM support**: Build and configure Windows-based VMs
- **Local ISO runs**: Testing and validation of local ISO builds
- **Cloud upload and sharing**: Automatic uploads to cloud storage with one-time download links, emailed to primary and CC'd contacts
- **Password change during configuration**: Allow password updates in configuration builds
- **Bundles**: Preconfigured flag sets for common VM types to simplify command invocation

## Project Structure

```
Kroltin/
├── kroltin/
│   ├── cli_args.py          # CLI argument parsing
│   ├── core.py              # Main application logic
│   ├── logger.py            # Logging configuration
│   ├── packer.py            # Packer integration
│   ├── run.py               # Entry points
│   ├── settings.py          # Settings management
│   ├── threaded_cmd.py      # Command execution
│   ├── golden_images/       # Stored golden images
│   ├── packer_templates/    # Packer HCL templates
│   ├── preseed-files/       # Preseed/kickstart files
│   └── scripts/             # Provisioning scripts
├── pyproject.toml           # Package configuration
├── install.sh               # Installation script
├── LICENSE.txt
└── README.md
```

## License

See [LICENSE.txt](LICENSE.txt) for details.

## Author

Duncan Woosley  
GitHub: [@d-woosley](https://github.com/d-woosley)