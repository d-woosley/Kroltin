import logging
import subprocess
import threading
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
        preseed_file=None,
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
        self.preseed_file = preseed_file
        self.export_path = export_path
        self.packer_template = packer_template
        self.logger = logging.getLogger(__name__)

    def _run_command_stream(self, cmd, cwd=None, env=None):
        """
        Run a command and stream stdout/stderr as lines arrive.

        Returns (returncode, stdout, stderr) where stdout/stderr are the
        captured full outputs (joined by newlines). Lines are printed to
        the process stdout/stderr as they arrive and also logged.
        """
        self.logger.debug("Executing command: %s", cmd)

        # Start the subprocess with pipes for stdout/stderr
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=cwd,
            env=env,
        )

        stdout_lines = []
        stderr_lines = []

        def _reader(pipe, collector, log_fn, is_err=False):
            try:
                for line in iter(pipe.readline, ''):
                    if line == '':
                        break
                    line = line.rstrip('\n')
                    collector.append(line)
                    # Mirror the line to the terminal immediately
                    print(line, flush=True)
                    # Also send to logger
                    try:
                        if is_err:
                            # keep error-level logging for stderr
                            self.logger.error(line)
                        else:
                            self.logger.info(line)
                    except Exception:
                        # Logging must not break streaming
                        pass
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass

        t_out = threading.Thread(target=_reader, args=(process.stdout, stdout_lines, self.logger.info, False))
        t_err = threading.Thread(target=_reader, args=(process.stderr, stderr_lines, self.logger.error, True))
        t_out.start()
        t_err.start()

        # Wait for threads to finish reading
        t_out.join()
        t_err.join()

        returncode = process.wait()

        return returncode, "\n".join(stdout_lines), "\n".join(stderr_lines)

    def build(self):
        """Build the VM image using HashiCorp Packer CLI."""
        self.logger.info(f"Starting build with ISOs: {self.iso_urls}, vmname: {self.vmname}, cpus: {self.cpus}, memory: {self.memory}, disk_size: {self.disk_size}, build_script: {self.preseed_file}, export_path: {self.export_path}")

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

        if self.preseed_file is not None:
            cmd += ['-var', f"preseed_file={self.preseed_file}"]

        if self.iso_urls:
            quoted = ",".join([f'\"{u}\"' for u in self.iso_urls])
            cmd += ['-var', f"iso_urls=[{quoted}]"]

        if self.scripts:
            quoted = ",".join([f'\"{u}\"' for u in self.scripts])
            cmd += ['-var', f"scripts=[{quoted}]"]

        # finally add the template
        cmd.append(self.packer_template)

        self.logger.info("Running Packer command: %s", ' '.join(cmd))
        returncode, stdout, stderr = self._run_command_stream(cmd)
        if returncode == 0:
            # Log both stdout and stderr for full diagnostics
            self.logger.info("Packer build completed successfully. stdout:\n%s\nstderr:\n%s", stdout, stderr)
            return True
        else:
            self.logger.error("Packer build failed (returncode=%s). stdout:\n%s\nstderr:\n%s", returncode, stdout, stderr)
            return False
    





