import logging
import subprocess
import os

class Packer:
    def __init__(
        self,
        iso_urls,
        vmname=None,
        cpus=None,
        memory=None,
        disk_size=None,
        ssh_username=None,
        ssh_password=None,
        iso_checksum=None,
        scripts=None,
        build_script=None,
        export_path=None,
        packer_template=None,
    ):
        """Create a VM image from a base ISO with custom configuration.

        Parameters mirror packer template variables.
        """
        self.iso_urls = iso_urls
        self.vmname = vmname
        self.cpus = cpus
        self.memory = memory
        self.disk_size = disk_size
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.iso_checksum = iso_checksum
        self.scripts = scripts or []
        self.build_script = build_script
        self.export_path = export_path
        self.packer_template = packer_template
        self.logger = logging.getLogger(__name__)

    def build(self):
        """Build the VM image using HashiCorp Packer CLI."""
        self.logger.info(f"Starting build with ISOs: {self.iso_urls}, vmname: {self.vmname}, cpus: {self.cpus}, memory: {self.memory}, disk_size: {self.disk_size}, build_script: {self.build_script}, export_path: {self.export_path}")

        if not os.path.exists(self.packer_template):
            self.logger.error(f"Packer template not found: {self.packer_template}")
            return False

        # Prepare build command
        cmd = ['packer', 'build']

        # Map parameters to -var flags expected by the template
        if self.vmname is not None:
            cmd += ['-var', f"name={self.vmname}"]
        if self.cpus is not None:
            cmd += ['-var', f"cpus={self.cpus}"]
        if self.memory is not None:
            cmd += ['-var', f"memory={self.memory}"]
        if self.disk_size is not None:
            cmd += ['-var', f"disk_size={self.disk_size}"]
        if self.ssh_username is not None:
            cmd += ['-var', f"ssh_username={self.ssh_username}"]
        if self.ssh_password is not None:
            cmd += ['-var', f"ssh_password={self.ssh_password}"]
        if self.iso_checksum is not None:
            cmd += ['-var', f"iso_checksum={self.iso_checksum}"]

        if self.iso_urls:
            quoted = ",".join([f'\"{u}\"' for u in self.iso_urls])
            cmd += ['-var', f"iso_urls=[{quoted}]"]

        if self.scripts:
            quoted = ",".join([f'\"{u}\"' for u in self.scripts])
            cmd += ['-var', f"scripts=[{quoted}]"]

        # finally add the template
        cmd.append(self.packer_template)

        self.logger.info(f"Running Packer command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Log both stdout and stderr for full diagnostics
            self.logger.info("Packer build completed successfully. stdout:\n%s\nstderr:\n%s", result.stdout, result.stderr)
            return True
        except subprocess.CalledProcessError as e:
            # CalledProcessError exposes returncode, stdout, stderr
            stdout = getattr(e, 'stdout', '')
            stderr = getattr(e, 'stderr', '')
            self.logger.error("Packer build failed (returncode=%s). stdout:\n%s\nstderr:\n%s", getattr(e, 'returncode', 'N/A'), stdout, stderr)
            return False
    





