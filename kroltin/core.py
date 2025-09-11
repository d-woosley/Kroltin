from kroltin.cli_args import load_args
from kroltin.logger import setup_logging
from kroltin.packer import Packer
import logging

class Kroltin:
    def __init__(self):
        self.args = load_args()
        self.logger = self._setup_logger()
        self.packer = Packer(
            vmname=self.args.vmname,
            vm_type=self.args.vm_type
        )

    def cli(self):
        if self.args.command == 'golden':
            result = self.packer.golden(
                packer_template=self.args.packer_template,
                iso_urls=self.args.iso_urls,
                cpus=self.args.cups,
                memory=self.args.memory,
                disk_size=self.args.disk_size,
                ssh_username=self.args.ssh_username,
                ssh_password=self.args.ssh_password,
                iso_checksum=self.args.iso_checksum,
                scripts=self.args.scripts,
                preseed_file=self.args.preseed_file,
                export_path=self.args.export_path,
            )
            self.logger.info(f"Packer golden build successful: {result}")
        elif self.args.command == 'configure':
            result = self.packer.configure(
                packer_template=self.args.packer_template,
                vm_file=self.args.vm_file,
                ssh_username=self.args.ssh_username,
                ssh_password=self.args.ssh_password,
                scripts=self.args.scripts,
                export_path=self.args.export_path,
            )
            self.logger.info(f"Packer configure successful: {result}")
        else:
            self.logger.info("Running Kroltin CLI")

    def web(self):
        self.logger.info("Running Kroltin Web Interface... not currently implemented.")
        pass

    def _setup_logger(self):
        setup_logging(self.args.debug, self.args.log, self.args.log_file)
        return logging.getLogger(__name__)