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

### Using Build Templates (Recommended)

Kroltin supports build templates for simplified command invocation. Templates store common configuration parameters so you don't need to specify them on every run.

**List available templates:**

```bash
kroltin-cli --list-templates
# or
kroltin-cli golden -lt
```

**Build using a template:**

```bash
kroltin-cli golden -t kali-latest --ssh-password kroltin
```

**Configure using a template:**

```bash
kroltin-cli configure -t kali-tailscale --ssh-password kroltin --tailscale-key tskey-abc123
```

Templates can include any command-line argument. You can override template values or provide missing required parameters (like `--ssh-password` and `--tailscale-key`) at runtime.

See [TEMPLATES.md](TEMPLATES.md) for detailed template documentation and how to create custom templates.

### Building a Golden Image

It's recommended to build a golden image first. Golden images can be reused for faster configuration runs later.

**Using a template:**

```bash
kroltin-cli golden -t kali-latest --ssh-password kroltin
```

**Using full command-line arguments:**

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

If no `--ssh-password` is provided, you will be prompted to enter one.

**Using a random password:**

For temporary VMs or testing, you can use the `--random-password` flag to generate a secure random password automatically:

```bash
kroltin golden -t kali-latest --random-password
```

The randomly generated password will be printed at the end of the build, after cleanup completes. This ensures the password is not lost in the build output. Example output:

```
  ######## Random SSH password for 'kali-base-2024': aB3$xY9!mN7@pQ2& ########
```

> ℹ️ The `--random-password` flag takes priority over `--ssh-password`. If both are provided, the random password will be used.

> ℹ️ Password changes during configuration builds are not yet supported.

### Configuring an Existing VM

Configuration builds are final products and cannot be saved back to the kroltin installation folder. They are exported to a specified path.

**Using a template:**

```bash
kroltin-cli configure -t kali-tailscale --ssh-password kroltin --tailscale-key tskey-abc123
```

**Using full command-line arguments:**

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
| `{{PASSWORD}}` | `--ssh-password` | SSH password in plaintext |
| `{{PASSWORD_CRYPT}}` | `--ssh-password` | SHA-512 crypt hash of the SSH password in unix `/etc/shadow` format |
| `{{RANDOM_PASSWORD}}` | Auto-generated | Randomly generated 16-character password (auto-generated when found in scripts) |
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

**Using `{{RANDOM_PASSWORD}}` in scripts:**

When `{{RANDOM_PASSWORD}}` is detected in any script, Kroltin automatically generates a secure 16-character random password and substitutes it into the script. The generated password is printed at the end of the build for your reference.

```bash
#!/bin/bash
# Create a temporary admin user with random password
useradd -m -s /bin/bash tempadmin
echo "tempadmin:{{RANDOM_PASSWORD}}" | chpasswd
echo "Temporary admin user created with random password"
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

List available build templates:

```bash
kroltin --list-templates
# or
kroltin-cli -lt
```

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
| `-lt, --list-templates` | List all available build templates |

### Golden Command

```bash
kroltin golden [OPTIONS]
```

**Template Options:**
- `-t, --template <NAME>`: Use a predefined build template
- `-lt, --list-templates`: List all available templates

**Required (if not using template):**
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
- `-rp, --random-password`: Generate a secure random 16-character password (takes priority over `--ssh-password`; printed at end of build)
- `--hostname <NAME>`: Hostname (default: uses `--vm-name`)
- `--tailscale-key <KEY>`: Tailscale authentication key for automatic network setup

**Scripts:**
- `--scripts <SCRIPT>...`: Scripts to run (space-separated)
- `--no-headless`: Show VM GUI during build

### Configure Command

```bash
kroltin configure [OPTIONS]
```

**Template Options:**
- `-t, --template <NAME>`: Use a predefined build template
- `-lt, --list-templates`: List all available templates

**Required (if not using template):**
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
- `-rp, --random-password`: Generate a secure random 16-character password (takes priority over `--ssh-password`; printed at end of build)
- `--hostname <NAME>`: Hostname (default: uses `--vm-name`)
- `--tailscale-key <KEY>`: Tailscale authentication key for automatic network setup

**Scripts:**
- `--scripts <SCRIPT>...`: Scripts to run (space-separated)
- `--no-headless`: Show VM GUI during configuration

## Recommendations

- **Use templates** for common build configurations to simplify command invocation
- Build golden images once and reuse them for faster configuration runs
- Use the `--scripts` flag to customize VMs with your own provisioning scripts
- Use `--random-password` for temporary VMs

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
│   ├── template_manager.py  # Build template management
│   ├── threaded_cmd.py      # Command execution
│   ├── templates.json       # Build template definitions
│   ├── golden_images/       # Stored golden images
│   ├── packer_templates/    # Packer HCL templates
│   ├── preseed-files/       # Preseed/kickstart files
│   └── scripts/             # Provisioning scripts
├── pyproject.toml           # Package configuration
├── install.sh               # Installation script
├── LICENSE.txt
├── README.md
└── TEMPLATES.md             # Template system documentation
```

## License

See [LICENSE.txt](LICENSE.txt) for details.

## Author

Duncan Woosley  
GitHub: [@d-woosley](https://github.com/d-woosley)