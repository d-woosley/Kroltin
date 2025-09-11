from kroltin.threaded_cmd import run_command_stream
import logging
import os

class Packer:
    def __init__(self, vmname=None, vm_type=None):
        """Packer helper.

        The constructor only stores the VM name. All other variables used by
        Packer CLI invocations are provided to the `golden` and `configure`
        methods (this keeps the init minimal as requested).
        """
        self.vmname = vmname
        self.vm_type = vm_type
        self.logger = logging.getLogger(__name__)

    def golden(
        self,
        packer_template,
        iso_urls=None,
        cpus=None,
        memory=None,
        disk_size=None,
        ssh_username=None,
        ssh_password=None,
        iso_checksum=None,
        scripts=None,
        preseed_file=None,
        export_path=None,
    ):
        """Build the VM image (golden image) using HashiCorp Packer CLI.

        This maps the Packer variables expected by an ISO-based template.
        """
        self.logger.info(
            "Starting golden build with ISOs: %s, vmname: %s, vm_type: %s, cpus: %s, memory: %s, disk_size: %s, build_script: %s, export_path: %s",
            iso_urls,
            self.vmname,
            self.vm_type,
            cpus,
            memory,
            disk_size,
            preseed_file,
            export_path,
        )
        packer_varables = [
            f"\'name={self.vmname}\'",
            f"vm_type=[{self._map_sources(self.vm_type, build='golden')}]",
            f"cpus={cpus}",
            f"memory={memory}",
            f"disk_size={disk_size}",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"iso_checksum={iso_checksum}",
            f"preseed_file={preseed_file}",
            f"iso_urls=[{self._quote_list(iso_urls)}]",
            f"scripts=[{self._quote_list(scripts)}]",
            f"export_path={export_path}"
        ]
        self._check_file_exists(packer_template)
        cmd = self._build_packer_cmd(packer_varables, packer_template)
        return self._run_packer(cmd=cmd)

    def configure(
        self,
        packer_template,
        vm_file=None,
        ssh_username=None,
        ssh_password=None,
        scripts=None,
        export_path=None,
        ):
        """Configure an existing VM golden image using Packer.

        Expected variables in the template:
          - vm_file: path to the VM to import
          - name, ssh_username, ssh_password, scripts, export_path
        """
        self.logger.info(
            "Starting VM configure: %s, vmname: %s, vm_type: %s, scripts: %s, export_path: %s",
            vm_file,
            self.vmname,
            self.vm_type,
            scripts,
            export_path,
        )
        packer_varables = [
            f"\'name={self.vmname}\'",
            f"vm_file={vm_file}",
            f"vm_type=[{self._map_sources(self.vm_type, build='configure')}]",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"scripts=[{self._quote_list(scripts)}]",
            f"export_path={export_path}"
        ]
        self._check_file_exists(packer_template)
        cmd = self._build_packer_cmd(packer_varables, packer_template)
        return self._run_packer(cmd=cmd)    
    
    #################### Helper Methods ####################

    def _check_file_exists(self, path) -> bool:
        if not os.path.exists(path):
            self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        return True

    def _build_packer_cmd(self, packer_varables: list, packer_template: str) -> str:
        cmd = ["packer", "build"]
        for var in packer_varables:
            cmd += ["-var", var]
        cmd.append(packer_template)
        return cmd

    def _run_packer(self, cmd: list) -> None:
        self.logger.info("Running Packer command: %s", ' '.join(cmd))
        returncode, stdout, stderr = run_command_stream(cmd)
        if returncode == 0:
            self.logger.info("Packer golden build completed successfully. stdout:\n%s\nstderr:\n%s",
                stdout,
                stderr
            )
            return True
        else:
            self.logger.error("Packer golden build failed (returncode=%s). stdout:\n%s\nstderr:\n%s",
                returncode,
                stdout,
                stderr
            )
            return False
    
    def _quote_list(self, items: list) -> str:
        return ",".join([f'\"{u}\"' for u in items])
    
    def _map_sources(self, type: str, build: str) -> str:
        if build == "golden":
            mapping = {
                "vmware": "vmware-iso",
                "virtualbox": "virtualbox-iso",
                "hyperv": "hyperv-iso",
            }
        elif build == "configure":
            mapping = {
                "vmware": "vmware-vmx",
                "virtualbox": "virtualbox-ovf",
                "hyperv": "hyperv-vmcx",
            }
        else:
            raise ValueError(f"Unknown build_type: {build}")
        
        if type.lower() == "all":
            type = [f"\"source.{v}.vm\"" for v in mapping.values()]
            return ",".join(type)

        if type.lower() not in mapping:
            raise ValueError(f"Unsupported type '{type}' for build_type '{build}'")

        return f"source.{mapping.get(type.lower(), type)}.vm"