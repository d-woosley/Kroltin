import time
import os
from getpass import getpass
from argparse import ArgumentParser, ArgumentError

from kroltin.settings import KroltinSettings


def load_args():
    settings = KroltinSettings()
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

    # Settings subcommand for script and packer file management
    settings_parser = subparsers.add_parser(
        "settings",
        help="Manage scripts, packer templates, and golden images"
    )

    # Listing group
    listing_group = settings_parser.add_argument_group('Listing', 'List scripts, templates, and golden images')
    listing_group.add_argument(
        "-ls", "--list-all",
        dest="list_all",
        help="List all scripts, packer template files, and golden images",
        action="store_true",
        default=False
    )
    listing_group.add_argument(
        "-ls-s", "--list-scripts",
        dest="list_scripts",
        help="List available scripts",
        action="store_true",
        default=False
    )
    listing_group.add_argument(
        "-ls-t", "--list-templates",
        dest="list_packer_templates",
        help="List available packer templates",
        action="store_true",
        default=False
    )
    listing_group.add_argument(
        "-ls-g", "--list-golden-images",
        dest="list_golden_images",
        help="List available builds in the golden_images directory",
        action="store_true",
        default=False
    )

    # Adding group
    adding_group = settings_parser.add_argument_group('Adding', 'Add scripts and packer templates')
    adding_group.add_argument(
        "-as", "--add-script",
        dest="add_script",
        metavar="<SCRIPT_PATH>",
        help="Add a script to the available scripts",
        type=str,
        default=None
    )
    adding_group.add_argument(
        "-at", "--add-packer-template",
        dest="add_packer_template",
        metavar="<PACKER_TEMPLATE_PATH>",
        help="Add a packer template to the available packer templates",
        type=str,
        default=None
    )

    # Removing group
    removing_group = settings_parser.add_argument_group('Removing', 'Remove scripts, templates, and golden images')
    removing_group.add_argument(
        "-rm-s", "--rm-script",
        dest="remove_script",
        metavar="<SCRIPT_NAME>",
        help="Remove a script from the available scripts",
        type=str,
        default=None
    )
    removing_group.add_argument(
        "-rm-t", "--rm-packer-template",
        dest="remove_packer_template",
        metavar="<PACKER_TEMPLATE_NAME>",
        help="Remove a packer template from the available packer templates",
        type=str,
        default=None
    )
    removing_group.add_argument(
        "-rm-g", "--rm-golden-image",
        dest="remove_golden_image",
        metavar="<GOLDEN_IMAGE_NAME>",
        help="Remove a golden image from the golden_images directory (irreversible)",
        type=str,
        default=None
    )

    # Export group
    import_export_group = settings_parser.add_argument_group('Import/Export', 'Import or export golden images to/from a user-specified path')
    import_export_group.add_argument(
        "-exp-g", "--export-golden-image",
        dest="export_golden_image",
        metavar="<GOLDEN_IMAGE_NAME>",
        help="Export (copy) a golden image to the current directory or to a path specified by --export-path",
        type=str,
        default=None
    )
    import_export_group.add_argument(
        "--export-path",
        dest="export_golden_image_path",
        metavar="<DEST_PATH>",
        help="Destination path for exported golden image (default: current directory)",
        type=str,
        default="."
    )
    import_export_group.add_argument(
        "-im-g",
        "--import-golden-image",
        dest="import_golden_image",
        metavar="<GOLDEN_IMAGE_PATH>",
        help="Import a golden image VM from the given path into the golden_images directory",
        type=str,
        default=None
    )

    # Golden subcommand: build a new VM from ISO using packer
    golden_parser = subparsers.add_parser(
        "golden",
        help="Run a packer VM build (golden image)"
    )
    golden_parser.add_argument(
        "--vm-type",
        dest="vm_type",
        help="Type of VM to build (required): vmware, virtualbox, hyperv, all",
        type=str,
        choices=["vmware", "virtualbox", "hyperv", "all"],
        required=True
    )
    golden_parser.add_argument(
        "--packer-template",
        dest="packer_template",
        help="Path to the packer template file (HCL or JSON).",
        type=str,
        required=True
    )
    golden_parser.add_argument(
        "--iso",
        dest="iso_urls",
        required=True,
        nargs='+',
        help="One or more paths or URLs to ISO files to use for the build (pass multiple separated by space)"
    )
    golden_parser.add_argument(
        "--vmname",
        dest="vmname",
        help="Packer 'vmname' variable (default: kroltin-$DATE)",
        type=str,
        default=time.strftime('kroltin-%Y%m%d_%H%M%S')
    )
    golden_parser.add_argument(
        "--cpus",
        dest="cpus",
        help="Number of CPUs for the VM",
        type=int,
        default=2
    )
    golden_parser.add_argument(
        "--memory",
        dest="memory",
        help="Memory (MB) for the VM",
        type=int,
        default=2048
    )
    golden_parser.add_argument(
        "--disk-size",
        "-ds",
        dest="disk_size",
        help="Disk size (MB) for the VM",
        type=int,
        default=81920
    )
    golden_parser.add_argument(
        "--ssh-username",
        dest="ssh_username",
        help="SSH username for the VM (required)",
        type=str,
        required=True
    )
    golden_parser.add_argument(
        "--ssh-password",
        dest="ssh_password",
        help="SSH password for the VM (will prompt if omitted)",
        type=str,
        required=False
    )
    golden_parser.add_argument(
        "--iso-checksum",
        dest="iso_checksum",
        help="Checksum for the ISO (required)",
        type=str,
        required=True
    )
    golden_parser.add_argument(
        "--scripts",
        dest="scripts",
        nargs='*',
        help="Optional list of scripts to run (script name from scripts dir or path; space separated)",
        default=[]
    )
    golden_parser.add_argument(
        "-pf",
        "--preseed-file",
        dest="preseed_file",
        help="Custom preseed file to run during packer build",
        required=True
    )

    # Configure subcommand: take an existing VM, run configuration scripts, export new VM
    configure_parser = subparsers.add_parser(
        "configure",
        help="Configure an new VM image using an exsisting golden VM"
    )
    configure_parser.add_argument(
        "--vm-type",
        dest="vm_type",
        help="Type of VM to configure (required): vmware, virtualbox, hyperv, all",
        type=str,
        choices=["vmware", "virtualbox", "hyperv", "all"],
        required=True
    )
    configure_parser.add_argument(
        "--packer-template",
        dest="packer_template",
        help="Packer template name (from installed templates) or path to a template file.",
        type=str,
        required=True
    )
    configure_parser.add_argument(
        "--vm-file",
        dest="vm_file",
        help="Golden image name (from installed images) or path to a VM file to configure.",
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
        help="Optional list of scripts to run (script name from installed scripts or path; space separated)",
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

    # Validate script/template existence for add/remove operations
    def validate_file_exists(file_name, check_method):
        if file_name is None:
            return True
        if check_method(file_name):
            return True
        if os.path.isfile(file_name):
            return True
        parser.error(f"File '{file_name}' does not exist in Kroltin or local path.")

    # Check for add/remove script
    if getattr(args, 'add_script', None):
        validate_file_exists(args.add_script, settings.check_script_exists)
    if getattr(args, 'remove_script', None):
        validate_file_exists(args.remove_script, settings.check_script_exists)

    # Check for add/remove packer template
    if getattr(args, 'add_packer_template', None):
        validate_file_exists(args.add_packer_template, settings.check_packer_template_exists)
    if getattr(args, 'remove_packer_template', None):
        validate_file_exists(args.remove_packer_template, settings.check_packer_template_exists)

    # Check all scripts in --scripts for existence
    if getattr(args, 'command', None) in ('golden', 'configure'):
        if getattr(args, 'packer_template', None):
            validate_file_exists(args.packer_template, settings.check_packer_template_exists)
        if getattr(args, 'scripts', None):
            for script in args.scripts:
                validate_file_exists(script, settings.check_script_exists)

        # Prompt for ssh password if missing
        if not getattr(args, 'ssh_password', None):
            try:
                args.ssh_password = getpass(prompt='SSH password: ')
            except (KeyboardInterrupt, EOFError):
                print('')
                raise

    return(args)