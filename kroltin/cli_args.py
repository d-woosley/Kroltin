import time
import os
import secrets
import string
from getpass import getpass
from argparse import ArgumentParser
import logging

from kroltin.settings import KroltinSettings


class ArgsValidator:
    """Build CLI parser and validate parsed CLI args using KroltinSettings.

    All helper methods are internal (single-responsibility). The module-level
    `load_args()` function remains the public entry point.
    """

    def __init__(self, settings: KroltinSettings):
        self.settings = settings
        self.parser = None
        self.logger = logging.getLogger(__name__)

        self.description = "A Command and Control (C2) service for penetration testing"
        self.epilog = "by: Duncan Woosley (github.com/d-woosley)"

    def load_args(self):
        """Build parser, parse arguments and validate them, then return args."""
        self._build_parser()
        self.args = self.parser.parse_args()
        self._validate()
        return self.args

    # ----------------------------------------------------------------------
    # Parser construction
    # ----------------------------------------------------------------------

    def _build_parser(self):
        """Create and return a configured ArgumentParser instance."""
        parser = ArgumentParser(description=self.description, epilog=self.epilog)

        timestamp = time.strftime('%Y%m%d_%H%M%S')

        self._add_global_args(parser)
        
        # Create parent parser for shared template variable arguments
        template_vars_parser = ArgumentParser(add_help=False)
        self._add_template_variable_args(template_vars_parser)
        
        subparsers = parser.add_subparsers(dest="command", required=False)
        self._add_settings_subparser(subparsers)
        self._add_golden_subparser(subparsers, timestamp, template_vars_parser)
        self._add_configure_subparser(subparsers, timestamp, template_vars_parser)

        self.parser = parser
        return True

    def _add_template_variable_args(self, parser: ArgumentParser):
        """Add template variable arguments to a parser (shared by golden and configure)."""
        template_vars_group = parser.add_argument_group(
            'Template Variables',
            'Variables that can be used in preseed files and bash scripts via {{VARIABLE}} placeholders'
        )
        template_vars_group.add_argument(
            "--ssh-username",
            dest="ssh_username",
            help="SSH username for the VM (mapped to {{USERNAME}} in templates; default: kroltin)",
            type=str,
            default="kroltin"
        )
        template_vars_group.add_argument(
            "--ssh-password",
            dest="ssh_password",
            help="SSH password for the VM (mapped to {{PASSWORD_CRYPT}} in templates; will prompt if omitted)",
            type=str,
            required=False
        )
        template_vars_group.add_argument(
            "-rp",
            "--random-password",
            dest="random_password",
            help="Generate a random 30-character password (overrides --ssh-password)",
            action="store_true",
            default=False
        )
        template_vars_group.add_argument(
            "--hostname",
            dest="hostname",
            help="Hostname for the VM (mapped to {{HOSTNAME}} in templates; default: uses --vm-name)",
            type=str,
            required=False
        )

    def _add_global_args(self, parser: ArgumentParser):
        parser.add_argument(
            "-ls",
            dest="list",
            help="List all scripts, packer template files, and golden images",
            action="store_true",
            default=False
        )
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

    def _add_settings_subparser(self, subparsers):
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
        listing_group.add_argument(
            "-ls-p", "--list-preseed-files",
            dest="list_preseed_files",
            help="List available preseed files in the preseed-files directory",
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
        adding_group.add_argument(
            "-ap", "--add-preseed-file",
            dest="add_preseed_file",
            metavar="<PRESEED_FILE_PATH>",
            help="Add a preseed file to the available preseed files",
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
        removing_group.add_argument(
            "-rm-p", "--rm-preseed-file",
            dest="remove_preseed_file",
            metavar="<PRESEED_FILE_NAME>",
            help="Remove a preseed file from the available preseed files",
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

    def _add_golden_subparser(self, subparsers, timestamp, template_vars_parser):
        golden_parser = subparsers.add_parser(
            "golden",
            help="Run a packer VM build (golden image)",
            parents=[template_vars_parser]
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
            dest="isos",
            required=True,
            nargs='+',
            help="One or more paths or URLs to ISO files to use for the build (pass multiple separated by space)"
        )
        golden_parser.add_argument(
            "--vm-name",
            dest="vm_name",
            help="Virtual machine name (Default: kroltin-$DATE)",
            type=str,
            default=time.strftime('kroltin-%Y%m%d_%H%M%S')
        )
        golden_parser.add_argument(
            "--cpus",
            dest="cpus",
            help="Number of CPUs for the VM (default: 2)",
            type=int,
            default=2
        )
        golden_parser.add_argument(
            "--memory",
            dest="memory",
            help="Memory (MB) for the VM (default: 4096)",
            type=int,
            default=4096
        )
        golden_parser.add_argument(
            "--disk-size",
            "-ds",
            dest="disk_size",
            help="Disk size (MB) for the VM (default: 81920)",
            type=int,
            default=81920
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
        golden_parser.add_argument(
            "--no-headless",
            dest="headless",
            help="Run the configuration with a GUI (not in headless mode).",
            action="store_false",
            default=True
        )
        golden_parser.add_argument(
            "--guest-os-type",
            dest="guest_os_type",
            help="Guest OS type for the VM (default: debian_64)",
            type=str,
            default="debian_64"
        )
        golden_parser.add_argument(
            "--vmware-version",
            dest="vmware_version",
            help="VMware only: Virtual hardware version (default: 16)",
            type=int,
            default=16
        )

    def _add_configure_subparser(self, subparsers, timestamp, template_vars_parser):
        configure_parser = subparsers.add_parser(
            "configure",
            help="Configure an new VM image using an exsisting golden VM",
            parents=[template_vars_parser]
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
            "--vm-name",
            dest="vm_name",
            help="Virtual machine name (Default: kroltin-$DATE)",
            type=str,
            default=time.strftime('kroltin-%Y%m%d_%H%M%S')
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
        configure_parser.add_argument(
            "--no-headless",
            dest="headless",
            help="Run the configuration with a GUI (not in headless mode).",
            action="store_false",
            default=True
        )
        configure_parser.add_argument(
            "--export-file-type",
            dest="export_file_type",
            help="Export file type: ova, ovf, or vmx (vmx is VMware only)",
            type=str,
            choices=["ova", "ovf", "vmx"],
            default="ova"
        )

    # ----------------------------------------------------------------------
    # Validation helpers
    # ----------------------------------------------------------------------

    def _validate_file_exists(self, file_name, check_method):
        if file_name is None:
            return True
        if check_method(file_name):
            return True
        if os.path.isfile(file_name):
            return True
        # Use parser.error so the program exits consistently with argparse behavior
        self.parser.error(f"File '{file_name}' does not exist in Kroltin or local path.")

    def _validate_add_remove(self, args):
        if getattr(args, 'add_script', None):
            self._validate_file_exists(args.add_script, self.settings.check_script_exists)
        if getattr(args, 'remove_script', None):
            self._validate_file_exists(args.remove_script, self.settings.check_script_exists)

        if getattr(args, 'add_packer_template', None):
            self._validate_file_exists(args.add_packer_template, self.settings.check_packer_template_exists)
        if getattr(args, 'remove_packer_template', None):
            self._validate_file_exists(args.remove_packer_template, self.settings.check_packer_template_exists)

        if getattr(args, 'add_preseed_file', None):
            self._validate_file_exists(args.add_preseed_file, lambda p: os.path.isfile(p))
        if getattr(args, 'remove_preseed_file', None):
            self._validate_file_exists(args.remove_preseed_file, lambda p: os.path.isfile(p))

    def _validate_command_specific(self, args):
        if getattr(args, 'command', None) in ('golden', 'configure'):
            if getattr(args, 'packer_template', None):
                self._validate_file_exists(args.packer_template, self.settings.check_packer_template_exists)
            if getattr(args, 'scripts', None):
                for script in args.scripts:
                    self._validate_file_exists(script, self.settings.check_script_exists)

            # Set hostname to vm_name if not provided
            if not getattr(args, 'hostname', None):
                args.hostname = getattr(args, 'vm_name', 'kroltin')

            # If random password requested, generate and use it
            if getattr(args, 'random_password', False):
                alphabet = string.ascii_letters + string.digits + string.punctuation
                args.ssh_password = ''.join(secrets.choice(alphabet) for _ in range(30))
            else:
                # Prompt for ssh password if missing
                if not getattr(args, 'ssh_password', None):
                    try:
                        args.ssh_password = getpass(prompt='SSH password: ')
                    except (KeyboardInterrupt, EOFError):
                        print('')
                        raise

    def _ensure_action_specified(self, args):
        if getattr(args, 'command', None) is None and not getattr(args, 'list', False):
            self.parser.error("No action requested, add -h for help.")

    def _validate(self):
        """Run all internal validation steps in sequence."""
        self._validate_add_remove(self.args)
        self._validate_command_specific(self.args)
        self._ensure_action_specified(self.args)


def load_args():
    settings = KroltinSettings()
    validator = ArgsValidator(settings)
    return validator.load_args()