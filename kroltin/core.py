from kroltin.cli_args import load_args
from kroltin.logger import setup_logging
import logging

class Kroltin:
    def __init__(self):
        pass

    def cli(self):
        args = load_args()

        # Setup logging (add log and log_file to CLI args as needed)
        debug = getattr(args, 'debug', False)
        log = getattr(args, 'log', False) if hasattr(args, 'log') else False
        log_file = getattr(args, 'log_file', 'kroltin.log') if hasattr(args, 'log_file') else 'kroltin.log'
        setup_logging(debug, log, log_file)
        logger = logging.getLogger(__name__)

        if getattr(args, 'command', None) == 'build':
            from kroltin.packer import Packer
            # Initialize Packer with CLI-provided variables
            packer = Packer(
                iso_urls=getattr(args, 'iso_urls', None),
                vmname=getattr(args, 'vmname', None),
                cpus=getattr(args, 'cpus', None),
                memory=getattr(args, 'memory', None),
                disk_size=getattr(args, 'disk_size', None),
                ssh_username=getattr(args, 'ssh_username', None),
                ssh_password=getattr(args, 'ssh_password', None),
                iso_checksum=getattr(args, 'iso_checksum', None),
                scripts=getattr(args, 'scripts', []),
                preseed_file=getattr(args, 'preseed_file', None),
                export_path=getattr(args, 'export_path', None),
                packer_template=getattr(args, 'packer_template', None)
            )
            result = packer.build()
            logger.info(f"Packer build successful: {result}")
        else:
            logger.info("Running Kroltin CLI")

    def web(self):
        print("Running Kroltin Web")