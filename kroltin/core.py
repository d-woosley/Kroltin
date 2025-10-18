from kroltin.cli_args import load_args
from kroltin.logger import setup_logging
from kroltin.packer import Packer
from kroltin.settings import KroltinSettings

import logging


class Kroltin:
    def __init__(self):
        self.args = load_args()
        self.logger = self._setup_logger()
        self.packer = Packer()

    def cli(self):
        if self.args.list:
            settings = KroltinSettings()
            settings.list_all()
            return

        if self.args.command == 'settings':
            settings = KroltinSettings()
            if self.args.list_all:
                settings.list_all()
            elif self.args.list_scripts:
                settings.list_scripts()
            elif self.args.list_packer_templates:
                settings.list_packer_templates()
            elif self.args.list_golden_images:
                settings.list_golden_images()
            elif self.args.list_preseed_files:
                settings.list_preseed_files()
            elif self.args.import_golden_image:
                settings.import_golden_image(self.args.import_golden_image)
            elif self.args.export_golden_image:
                image_name = self.args.export_golden_image
                dest_path = self.args.export_golden_image_path
                settings.export_golden_image(image_name, dest_path)
            elif self.args.remove_golden_image:
                settings.remove_golden_image(self.args.remove_golden_image)
            elif self.args.add_script:
                self.logger.info(f"Adding script: {self.args.add_script}")
                if settings.add_script(self.args.add_script):
                    self.logger.info("Script added successfully.")
                    settings.list_scripts()
                else:
                    self.logger.error("Failed to add script.")
            elif self.args.remove_script:
                self.logger.info(f"Removing script: {self.args.remove_script}")
                if settings.remove_script(self.args.remove_script):
                    self.logger.info("Script removed successfully.")
                    settings.list_scripts()
                else:
                    self.logger.error("Failed to remove script.")
            elif self.args.add_packer_template:
                self.logger.info(f"Adding packer template: {self.args.add_packer_template}")
                if settings.add_packer_template(self.args.add_packer_template):
                    self.logger.info("Packer template added successfully.")
                    settings.list_packer_templates()
                else:
                    self.logger.error("Failed to add packer template.")
            elif self.args.remove_packer_template:
                self.logger.info(f"Removing packer template: {self.args.remove_packer_template}")
                if settings.remove_packer_template(self.args.remove_packer_template):
                    self.logger.info("Packer template removed successfully.")
                    settings.list_packer_templates()
                else:
                    self.logger.error("Failed to remove packer template.")
            elif self.args.add_preseed_file:
                self.logger.info(f"Adding preseed file: {self.args.add_preseed_file}")
                if settings.add_preseed_file(self.args.add_preseed_file):
                    self.logger.info("Preseed file added successfully.")
                    settings.list_preseed_files()
                else:
                    self.logger.error("Failed to add preseed file.")
            elif self.args.remove_preseed_file:
                self.logger.info(f"Removing preseed file: {self.args.remove_preseed_file}")
                if settings.remove_preseed_file(self.args.remove_preseed_file):
                    self.logger.info("Preseed file removed successfully.")
                    settings.list_preseed_files()
                else:
                    self.logger.error("Failed to remove preseed file.")
        elif self.args.command == 'golden':
            if self.packer.golden(
                packer_template=self.args.packer_template,
                vm_name=self.args.vm_name,
                vm_type=self.args.vm_type,
                isos=self.args.isos,
                cpus=self.args.cpus,
                memory=self.args.memory,
                disk_size=self.args.disk_size,
                ssh_username=self.args.ssh_username,
                ssh_password=self.args.ssh_password,
                hostname=self.args.hostname,
                iso_checksum=self.args.iso_checksum,
                scripts=self.args.scripts,
                preseed_file=self.args.preseed_file,
                headless=self.args.headless,
                guest_os_type=self.args.guest_os_type,
                vmware_version=self.args.vmware_version,
                random_password=self.args.random_password
            ):
                self.logger.info(f"Golden Image build successful!")
        elif self.args.command == 'configure':
            if self.packer.configure(
                packer_template=self.args.packer_template,
                vm_name=self.args.vm_name,
                vm_type=self.args.vm_type,
                vm_file=self.args.vm_file,
                ssh_username=self.args.ssh_username,
                ssh_password=self.args.ssh_password,
                hostname=self.args.hostname,
                scripts=self.args.scripts,
                export_path=self.args.export_path,
                headless=self.args.headless,
                export_file_type=self.args.export_file_type,
                random_password=self.args.random_password
            ):
                self.logger.info(f"VM configurion successful!")
        else:
            self.logger.info("Running Kroltin CLI")

    def web(self):
        self.logger.info("Running Kroltin Web Interface... not currently implemented.")
        pass

    def _setup_logger(self):
        setup_logging(self.args.debug, self.args.log, self.args.log_file)
        return logging.getLogger(__name__)