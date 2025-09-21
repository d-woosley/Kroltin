from kroltin.threaded_cmd import run_command_stream
import logging
from os import path, remove
import tempfile
import importlib.resources as resources
import pathlib
import time
import shutil
import hashlib


class Packer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.timestamp = time.strftime('%Y%m%d_%H%M%S')

        # Directories within the installed package
        self.scripts_dir = str(resources.files('kroltin') / 'scripts')
        self.golden_images_dir = str(resources.files('kroltin') / 'golden_images')
        self.http_directory = str(resources.files('kroltin') / 'preseed-files')
        self.temp_dir = tempfile.gettempdir()

    # ----------------------------------------------------------------------
    # VM Build Methods
    # ----------------------------------------------------------------------

    def golden(
        self,
        packer_template,
        vm_name=None,
        vm_type=None,
        isos=None,
        cpus=None,
        memory=None,
        disk_size=None,
        ssh_username=None,
        ssh_password=None,
        iso_checksum=None,
        scripts=None,
        preseed_file=None,
    ) -> bool:
        """Build the VM image (golden image) using HashiCorp Packer CLI.

        This maps the Packer variables expected by an ISO-based template.
        """
        self.logger.debug(
            "Starting golden build with ISOs: %s, vm_name: %s, vm_type: %s, cpus: %s, "
            "memory: %s, disk_size: %s, ssh_username %s, build_script: %s, "
            "iso_checksum: %s, preseed_file: %s",
            str(isos), vm_name, vm_type, str(cpus), str(memory), str(disk_size),
            ssh_username, str(scripts), iso_checksum, preseed_file
        )

        self._fill_pressed(
            preseed_file=self._resolve_file_path(
                preseed_file,
                self.http_directory
            ),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            hostname=vm_name
        )

        packer_varables = [
            f"name={vm_name}",
            f"vm_type=[\"{self._map_sources(vm_type, build='golden')}\"]",
            f"cpus={cpus}",
            f"memory={memory}",
            f"disk_size={disk_size}",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"iso_checksum={iso_checksum}",
            f"preseed_file={self.filled_preseed_name}",
            f"http_directory={self.http_directory}",
            f"isos=[{self._quote_list(isos)}]",
            f"scripts=[{self._quote_list(self._resolve_scripts(scripts))}]",
            f"export_path={self.golden_images_dir}",
            f"build_path={self._build_path(vm_name)}"
        ]

        resolved_template = self._resolve_packer_template(packer_template)
        cmd = self._build_packer_cmd(packer_varables, resolved_template)
        try:
            if self._run_packer(cmd):
                self._get_build_hash(vm_name)
                self._remove_filled_preseed()
                self._remove_build_path(vm_name)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error during golden build: {e}")
            self._remove_filled_preseed()
            self._remove_build_path(vm_name)
            return False

    def configure(
        self,
        packer_template: str,
        vm_name: str,
        vm_type: str,
        vm_file: str,
        ssh_username: str = None,
        ssh_password: str = None,
        scripts: list = None,
        export_path: str = None,
        ) -> bool:
        """Configure an existing VM golden image using Packer."""
        self.logger.debug(
            "Starting VM configure: %s, vm_name: %s, vm_type: %s, scripts: %s, "
            "export_path: %s",
            vm_file, vm_name, vm_type, str(scripts), export_path
        )

        packer_varables = [
            f"name={vm_name}",
            f"vm_file={self._resolve_file_path(vm_file, self.golden_images_dir)}",
            f"vm_type=[\"{self._map_sources(vm_type, build='configure')}\"]",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"scripts=[{self._quote_list(self._resolve_scripts(scripts))}]",
            f"export_path={export_path}",
            f"build_path={self._build_path(vm_name)}"
        ]
        
        resolved_template = self._resolve_packer_template(packer_template)
        cmd = self._build_packer_cmd(packer_varables, resolved_template)

        try:
            if self._run_packer(cmd):
                self._get_build_hash(vm_name)
                self._remove_build_path(vm_name)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error during VM configure: {e}")
            self._remove_build_path(vm_name)
            return False
    
    # ----------------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------------

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
    
    def _get_build_hash(self, vm_name: str) -> str:
        """Set the instance variables for MD5, SHA1, and SHA256 hashes from the .kroltin_build temporary directory"""
        ova_path = path.join(self.temp_dir, f"{vm_name}.ova")
        self._check_file_exists(ova_path)

        self.md5_hash = self._compute_file_hash(ova_path, algorithm='md5')
        self.sha1_hash = self._compute_file_hash(ova_path, algorithm='sha1')
        self.sha256_hash = self._compute_file_hash(ova_path, algorithm='sha256')

        self.logger.debug(f"Computed hashes for {ova_path} - MD5: {self.md5_hash}, SHA1: {self.sha1_hash}, SHA256: {self.sha256_hash}")
        return True

    def _compute_file_hash(file_path, algorithm='sha256'):
        """Compute the hash of a file using the specified algorithm."""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()

    # ----------------------------------------------------------------------
    # File Resolution Helper Methods
    # ----------------------------------------------------------------------

    def _check_file_exists(self, file_path) -> bool:
        self.logger.debug(f"Checking if file exists: {file_path}")
        if not path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        return True

    def _build_path(self, vm_name: str) -> str:
        """Return the build path for a given VM name in the system temp directory."""
        self.logger.debug(f"Temporary build path for VM '{vm_name}': {self.temp_dir}/{vm_name}")
        return f"{self.temp_dir}/{vm_name}"

    def _resolve_file_path(self, file_name: str, kroltin_dir: str) -> str:
        """Return the absolute path, checking kroltin directoires first, then user path. Transfer to kroltin_dir if needed."""
        kroltin_path = self._resolve_file(file_name, kroltin_dir)
        if kroltin_path:
            return kroltin_path
        
        user_path = self._find_user_file(file_name)
        if user_path:
            return user_path
        
        self.logger.warning(f"File '{file_name}' not found in kroltin directories or at user path.")
        return False

    def _resolve_file(self, file_name: str, search_dir: str) -> str:
        """Return the absolute path to file name in search_dir, else check user path, else None."""
        file_in_dir = path.join(search_dir, path.basename(file_name))
        if path.isfile(file_in_dir):
            return file_in_dir
        elif path.isfile(file_name):
            return path.abspath(file_name)
        return None

    def _find_user_file(self, file_name: str) -> str:
        """Return the absolute path to the user-supplied VM file if it exists, else None."""
        user_path = pathlib.Path(file_name)
        if user_path.exists():
            return str(user_path.resolve())
        return None

    def _resolve_scripts(self, scripts: list) -> list:
        """Return a list of absolute paths for scripts, checking scripts dir first, then user path."""
        resolved = []
        for script in scripts:
            script_path = self._resolve_file(script, self.scripts_dir)
            if script_path:
                resolved.append(script_path)
            else:
                self.logger.warning(f"Script '{script}' not found in scripts dir or at user path.")
                return False
        return resolved

    def _resolve_packer_template(self, template_name: str) -> str:
        """Return the absolute path to the packer template, checking installed dir first, then user path."""
        templates_dir = str(resources.files('kroltin') / 'packer_templates')
        resolved = self._resolve_file(template_name, templates_dir)
        if resolved:
            return resolved
        self.logger.error(f"Packer template '{template_name}' not found in packer_templates dir or at user path.")
        raise FileNotFoundError(f"Packer template '{template_name}' not found in packer_templates dir or at user path.")

    # ----------------------------------------------------------------------
    # Packer Template Management
    # ----------------------------------------------------------------------

    def init_template(self, packer_template: str) -> bool:
        """Run 'packer init' on the given Packer template."""
        self._check_file_exists(packer_template)
        cmd = self._build_packer_cmd([], packer_template, base_cmd=["packer", "init"])
        return self._run_packer(cmd)

    def validate_template(self, packer_template: str) -> bool:
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
            "isos=[\"dummy.iso\"]",
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
    
    # ----------------------------------------------------------------------
    # Preseed File Handling
    # ----------------------------------------------------------------------

    def _fill_pressed(self,
            preseed_file: str,
            ssh_username: str,
            ssh_password: str,
            hostname: str
        ) -> str:
        """Fill in the preseed file with the provided SSH username and password."""
        self.filled_preseed_name = f"filled_{self.timestamp}_{path.basename(preseed_file)}"
        self.filled_preseed_path = path.join(
            self.http_directory, 
            self.filled_preseed_name
        )
        
        try:
            with open(preseed_file, 'r') as infile, open(self.filled_preseed_path, 'w') as outfile:
                for line in infile:
                    if ssh_username:
                        line = line.replace('{{USERNAME}}', ssh_username)
                    if ssh_password:
                        line = line.replace('{{PASSWORD}}', ssh_password)
                    if hostname:
                        line = line.replace('{{HOSTNAME}}', hostname)
                    outfile.write(line)
            self.logger.info(f"Filled preseed file created at: {self.filled_preseed_path}")
            return True 
        except Exception as e:
            self.logger.error(f"Error filling preseed file: {e}")
            raise e
        
    def _remove_filled_preseed(self):
        """Remove the filled preseed file if it exists."""
        if hasattr(self, 'filled_preseed_path') and path.exists(self.filled_preseed_path):
            try:
                remove(self.filled_preseed_path)
                self.logger.debug(f"Removed filled preseed file: {self.filled_preseed_path}")
            except Exception as e:
                self.logger.error(f"Error removing filled preseed file: {e}")

    def _remove_build_path(self, vm_name: str):
        """Remove the temporary build path if it exists."""
        build_path = self._build_path(vm_name)
        if path.exists(build_path):
            try:
                shutil.rmtree(build_path)
                self.logger.debug(f"Removed build path: {build_path}")
            except Exception as e:
                self.logger.error(f"Error removing build path: {e}")