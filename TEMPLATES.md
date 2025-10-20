# Build Templates

Kroltin now supports pre-configured build templates for common VM configurations. Templates simplify the build process by providing pre-configured settings for golden image builds and VM configurations.

## Using Templates

### List Available Templates

To see all available templates:

```bash
kroltin-cli --list-templates
# or
kroltin-cli -lt
```

Templates are also shown when using the general list command:

```bash
kroltin-cli -ls
```

Or within the configure command:

```bash
kroltin-cli configure --list
```

### Using a Template for Golden Image Build

To build a VM using a template:

```bash
kroltin-cli golden --template kali-latest
# or
kroltin-cli golden -t kali-latest
```

The template will provide default values for:
- ISO file(s) and checksums
- Preseed configuration file
- VM specifications (CPU, memory, disk size)
- Scripts to run
- Packer template to use
- VM Types (VMware, VirtualBox... ect.)

You can override any template value by providing it as a CLI argument:

```bash
kroltin-cli golden -t kali-latest --vm-type vmware --cpus 4 --memory 8192
```

### Using a Template for VM Configuration

To configure an existing VM using a template:

```bash
kroltin-cli configure --template kali-tailscale
# or
kroltin-cli configure -t kali-tailscale
```

## Creating Custom Templates

Templates are stored in `kroltin/templates.json`. To add a custom template:

1. Edit the `templates.json` file
2. Add your template under the `templates` key
3. Specify the template type (`golden` or `configure`)
4. Provide default configuration values

### Template Structure

**Golden Template Example:**
```json
{
  "my-custom-template": {
    "name": "My Custom VM",
    "description": "Description of the VM",
    "type": "golden",
    "config": {
      "vm_type": "vmware",
      "packer_template": "build.pkr.hcl",
      "iso": ["https://example.com/os.iso"],
      "iso_checksum": "sha256:abc123...",
      "preseed_file": "my-preseed.cfg",
      "vm_name": "my-custom-vm",
      "cpus": 2,
      "memory": 4096,
      "disk_size": 81920,
      "guest_os_type": "debian_64",
      "vmware_version": 16,
      "headless": true,
      "scripts": ["script1.sh", "script2.sh"]
    }
  }
}
```

**Configure Template Example:**
```json
{
  "my-config-template": {
    "name": "My VM Configuration",
    "description": "Configures an existing VM",
    "type": "configure",
    "config": {
      "vm_type": "vmware",
      "packer_template": "configure.pkr.hcl",
      "vm_file": "my-golden-image",
      "vm_name": "my-configured-vm",
      "headless": true,
      "export_file_type": "ova",
      "scripts": ["config-script.sh"]
    }
  }
}
```

## Notes

- CLI arguments always override template values
- Templates can reference files in the Kroltin package directories (scripts, preseed files, etc.)
- SSH credentials are still required and must be provided via CLI arguments or prompts
