import time
from getpass import getpass
from argparse import ArgumentParser


def load_args():
    parser = ArgumentParser(
        description="A Command and Control (C2) service for penetration testing",
        epilog="by: Duncan Woosley (github.com/d-woosley)",
    )

    timestamp = time.strftime('%Y%m%d_%H%M%S')

    # Add global arguments
    parser.add_argument(
        '-d',
        "--debug",
        dest="debug",
        help="Set output to debug",
        action="store_true",
        default=False
    )
    parser.add_argument(
        '-l',
        '--log',
        dest="log",
        help="Enable logging to a file",
        action="store_true",
        default=False
    )
    parser.add_argument(
        '-lf',
        '--log-file',
        dest="log_file",
        metavar="<LOG_FILE>",
        help="Path to save log to a file (default: kroltin.log)",
        type=str,
        default="kroltin.log"
    )

    # Add subparsers
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Golden subcommand: build a new VM from ISO using packer
    build_parser = subparsers.add_parser(
        "golden",
        help="Run a packer VM build (golden image)"
    )
    build_parser.add_argument(
        "--vm-type",
        dest="vm_type",
        help="Type of VM to build (required): vmware, virtualbox, hyperv, aws, azure, gcp",
        type=str,
        choices=["vmware", "virtualbox", "hyperv", "aws", "azure", "gcp"],
        required=True
    )
    build_parser.add_argument(
        "--packer-template",
        dest="packer_template",
        help="Path to the packer template file (HCL or JSON).",
        type=str,
        required=True
    )
    build_parser.add_argument(
        "--iso",
        dest="iso_urls",
        required=True,
        nargs='+',
        help="One or more paths or URLs to ISO files to use for the build (pass multiple separated by space)"
    )
    # Map Packer variables to CLI options
    build_parser.add_argument(
        "--vmname",
        dest="vmname",
        help="Packer 'vmname' variable (default: kroltin-$DATE)",
        type=str,
        default=time.strftime('kroltin-%Y%m%d_%H%M%S')
    )
    build_parser.add_argument(
        "--cpus",
        dest="cpus",
        help="Number of CPUs for the VM",
        type=int,
        default=2
    )
    build_parser.add_argument(
        "--memory",
        dest="memory",
        help="Memory (MB) for the VM",
        type=int,
        default=2048
    )
    build_parser.add_argument(
        "--disk-size",
        "-ds",
        dest="disk_size",
        help="Disk size (MB) for the VM",
        type=int,
        default=81920
    )
    build_parser.add_argument(
        "--ssh-username",
        dest="ssh_username",
        help="SSH username for the VM (required)",
        type=str,
        required=True
    )
    build_parser.add_argument(
        "--ssh-password",
        dest="ssh_password",
        help="SSH password for the VM (will prompt if omitted)",
        type=str,
        required=False
    )
    build_parser.add_argument(
        "--iso-checksum",
        dest="iso_checksum",
        help="Checksum for the ISO (required)",
        type=str,
        required=True
    )
    build_parser.add_argument(
        "--scripts",
        dest="scripts",
        nargs='*',
        help="Optional list of scripts to pass to the packer build (space separated)",
        default=[]
    )
    build_parser.add_argument(
        "-pf",
        "--preseed-file",
        dest="preseed_file",
        help="Custom preseed file to run during packer build",
        required=True
    )
    build_parser.add_argument(
        "--export-path",
        dest="export_path",
        default=f"kroltin_vm_{timestamp}",
        help="Optional export path for the built VM (default: kroltin_vm_TIMESTAMP)"
    )

    # Configure subcommand: take an existing OVF, run configuration scripts, export new OVF
    configure_parser = subparsers.add_parser(
        "configure",
        help="Configure an existing OVF/OVA using the VirtualBox OVF/OVA packer builder"
    )
    configure_parser.add_argument(
        "--vm-type",
        dest="vm_type",
        help="Type of VM to configure (required): vmware, virtualbox, hyperv, aws, azure, gcp",
        type=str,
        choices=["vmware", "virtualbox", "hyperv", "aws", "azure", "gcp"],
        required=True
    )
    configure_parser.add_argument(
        "--packer-template",
        dest="packer_template",
        help="Path to the packer template file (HCL or JSON).",
        type=str,
        required=True
    )
    configure_parser.add_argument(
        "--ovf-file",
        dest="ovf_file",
        help="Path to the OVF/OVA file to import",
        type=str,
        required=True
    )
    configure_parser.add_argument(
        "--vmname",
        dest="vmname",
        help="Packer 'vmname' variable (optional)",
        type=str,
        default=time.strftime('kroltin-%Y%m%d_%H%M%S')
    )
    configure_parser.add_argument(
        "--ssh-username",
        dest="ssh_username",
        help="SSH username for the VM (required)",
        type=str,
        required=True
    )
    configure_parser.add_argument(
        "--ssh-password",
        dest="ssh_password",
        help="SSH password for the VM (will prompt if omitted)",
        type=str,
        required=False
    )
    configure_parser.add_argument(
        "--scripts",
        dest="scripts",
        nargs='*',
        help="Optional list of scripts to run inside the VM (space separated)",
        default=[]
    )
    configure_parser.add_argument(
        "--export-path",
        dest="export_path",
        default=f"kroltin_configured_vm_{timestamp}",
        help="Optional export path for the configured VM (default: kroltin_configured_vm_TIMESTAMP)"
    )

    # Get arg results
    args = parser.parse_args()

    if getattr(args, 'command', None) in ('golden', 'configure') and not args.ssh_password:
        while not args.ssh_password:
            try:
                args.ssh_password = getpass(prompt='SSH password: ')
            except (KeyboardInterrupt, EOFError):
                print('')
                raise

    return(args)