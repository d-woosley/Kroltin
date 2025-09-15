from kroltin.threaded_cmd import run_command_stream
import logging
import os
import importlib.resources as resources

class Packer:
    def __init__(self):
        """Packer helper.

        The constructor is minimal. All variables used by
        Packer CLI invocations are provided to the `golden` and `configure`
        methods.
        """
        self.logger = logging.getLogger(__name__)

    # ----------------------------------------------------------------------
    # VM Build Methods
    # ----------------------------------------------------------------------

    def golden(
        self,
        packer_template,
        vmname=None,
        vm_type=None,
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
        self.logger.debug(
            "Starting golden build with ISOs: %s, vmname: %s, vm_type: %s, cpus: %s, memory: %s, disk_size: %s, build_script: %s, export_path: %s",
            iso_urls,
            vmname,
            vm_type,
            cpus,
            memory,
            disk_size,
            preseed_file,
            export_path,
        )
        packer_varables = [
            f"'name={vmname}'",
            f"vm_type=[{self._map_sources(vm_type, build='golden')}]",
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
        vmname=None,
        vm_type=None,
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
        self.logger.debug(
            "Starting VM configure: %s, vmname: %s, vm_type: %s, scripts: %s, export_path: %s",
            vm_file,
            vmname,
            vm_type,
            scripts,
            export_path,
        )
        packer_varables = [
            f"'name={vmname}'",
            f"vm_file={vm_file}",
            f"vm_type=[{self._map_sources(vm_type, build='configure')}]",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"scripts=[{self._quote_list(scripts)}]",
            f"export_path={export_path}"
        ]
        self._check_file_exists(packer_template)
        cmd = self._build_packer_cmd(packer_varables, packer_template)
        return self._run_packer(cmd=cmd)    
    
    # ----------------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------------

    def _check_file_exists(self, path) -> bool:
        if not os.path.exists(path):
            self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        return True

    def _build_packer_cmd(self, packer_varables: list, packer_template: str, base_cmd=["packer", "build"],) -> str:
        cmd = base_cmd
        for var in packer_varables:
            cmd += ["-var", var]
        cmd.append(packer_template)
        return cmd

    def _run_packer(self, cmd: list) -> bool:
        returncode, stdout, stderr = run_command_stream(cmd)
        if returncode == 0:
            return True
        else:
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
    
    # ----------------------------------------------------------------------
    # Packer Template Management
    # ----------------------------------------------------------------------

    def init_template(self, packer_template):
        """Run 'packer init' on the given Packer template."""
        self._check_file_exists(packer_template)
        cmd = self._build_packer_cmd([], packer_template, base_cmd=["packer", "init"])
        return self._run_packer(cmd)

    def validate_template(self, packer_template):
        """Run 'packer validate' on the given Packer template, passing dummy/default variables."""
        self._check_file_exists(packer_template)

        # Get absolute path to test.sh in installed scripts dir
        test_script_path = str(resources.files('kroltin') / 'scripts' / 'test.sh')
        # Configure variables and defaults
        configure_vars = [
            "name=dummy_vm",
            "vm_file=dummy.vmx",
            "vm_type=[\"source.virtualbox-ovf.vm\"]",
            "ssh_username=dummyuser",
            "ssh_password=dummypass",
            f'scripts=["{test_script_path}"]',
            "export_path=dummy_export_path"
        ]
        # Golden variables and defaults
        golden_vars = [
            "name=dummy_vm",
            "vm_type=[\"source.virtualbox-iso.vm\"]",
            "cpus=2",
            "memory=2048",
            "disk_size=81920",
            "ssh_username=dummyuser",
            "ssh_password=dummypass",
            "iso_checksum=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "preseed_file=dummy_preseed.cfg",
            "iso_urls=[\"dummy.iso\"]",
            f'scripts=["{test_script_path}"]',
            "export_path=dummy_export_path"
        ]

        # Try configure variables first
        cmd = self._build_packer_cmd(configure_vars, packer_template, base_cmd=["packer", "validate"])
        if not self._run_packer(cmd):
            self.logger.debug("'packer validate' (configure vars) failed, trying golden vars.")
            cmd = self._build_packer_cmd(golden_vars, packer_template, base_cmd=["packer", "validate"])
            return self._run_packer(cmd)
        return True