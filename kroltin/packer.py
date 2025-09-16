from kroltin.threaded_cmd import run_command_stream
import logging
from os import path, listdir
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
            self._golden_image_path(),
        )
        resolved_scripts = self._resolve_scripts(scripts)
        packer_varables = [
            f"name={vmname}",
            f"vm_type=[\"{self._map_sources(vm_type, build='golden')}\"]",
            f"cpus={cpus}",
            f"memory={memory}",
            f"disk_size={disk_size}",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"iso_checksum={iso_checksum}",
            f"preseed_file={preseed_file}",
            f"iso_urls=[\"{self._quote_list(iso_urls)}\"]",
            f"scripts=[\"{self._quote_list(resolved_scripts)}\"]",
            f"export_path={self._golden_image_path()}"
        ]
        resolved_template = self._resolve_packer_template(packer_template)
        cmd = self._build_packer_cmd(packer_varables, resolved_template)
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

        vm_file_path = self._resolve_vm_file_path(vm_file)
        resolved_scripts = self._resolve_scripts(scripts)

        packer_varables = [
            f"name={vmname}",
            f"vm_file={vm_file_path}",
            f"vm_type=[\"{self._map_sources(vm_type, build='configure')}\"]",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"scripts=[{self._quote_list(resolved_scripts)}]",
            f"export_path={export_path}"
        ]
        resolved_template = self._resolve_packer_template(packer_template)
        cmd = self._build_packer_cmd(packer_varables, resolved_template)
        return self._run_packer(cmd=cmd)
    
    # ----------------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------------

    def _check_file_exists(self, file_path) -> bool:
        self.logger.debug(f"Checking if file exists: {file_path}")
        if not path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
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
    
    def _golden_image_path(self) -> str:
        """Return the export path for the built VM."""
        golden_images_path = resources.files(__package__).parent / 'golden_images'
        golden_images_path.mkdir(exist_ok=True)
        return str(golden_images_path)

    def _resolve_vm_file_path(self, vm_file):
        """Return the absolute path to the VM file, checking golden images first, then user path, else warn."""
        if not vm_file:
            self.logger.warning("No vm_file provided to configure().")
            return vm_file
        golden_path = self._find_golden_image(vm_file)
        if golden_path:
            return golden_path
        user_path = self._find_user_vm_file(vm_file)
        if user_path:
            return user_path
        self.logger.warning(f"VM file '{vm_file}' not found in golden_images or at user path.")
        return vm_file

    def _find_golden_image(self, vm_file):
        """Return the path to the golden image if it exists, else None."""
        golden_images_dir = str(resources.files('kroltin') / 'golden_images')
        return self._resolve_file(vm_file, golden_images_dir)
    
    def _resolve_file(self, filename, search_dir):
        """Return the absolute path to filename in search_dir, else check user path, else None."""
        file_in_dir = path.join(search_dir, path.basename(filename))
        if path.isfile(file_in_dir):
            return file_in_dir
        elif path.isfile(filename):
            return path.abspath(filename)
        return None

    def _find_user_vm_file(self, vm_file):
        """Return the absolute path to the user-supplied VM file if it exists, else None."""
        import pathlib
        user_path = pathlib.Path(vm_file)
        if user_path.exists():
            return str(user_path.resolve())
        return None

    def _resolve_scripts(self, scripts):
        """Return a list of absolute paths for scripts, checking scripts dir first, then user path."""
        if not scripts:
            return []
        scripts_dir = str(resources.files('kroltin') / 'scripts')
        resolved = []
        for script in scripts:
            script_path = self._resolve_file(script, scripts_dir)
            if script_path:
                resolved.append(script_path)
            else:
                self.logger.warning(f"Script '{script}' not found in scripts dir or at user path.")
                resolved.append(script)  # Pass as-is, but warn
        return resolved

    def _resolve_packer_template(self, template):
        """Return the absolute path to the packer template, checking installed dir first, then user path."""
        templates_dir = str(resources.files('kroltin') / 'packer_templates')
        resolved = self._resolve_file(template, templates_dir)
        if resolved:
            return resolved
        self.logger.error(f"Packer template '{template}' not found in packer_templates dir or at user path.")
        raise FileNotFoundError(f"Packer template '{template}' not found in packer_templates dir or at user path.")

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