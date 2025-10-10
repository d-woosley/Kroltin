from kroltin.threaded_cmd import CommandRunner
import logging
import os
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
        self.cmd_runner = CommandRunner()

        # Directories within the installed package
        self.scripts_dir = str(resources.files('kroltin').joinpath('scripts'))
        self.golden_images_dir = str(resources.files('kroltin').joinpath('golden_images'))
        self.preseed_dir = str(resources.files('kroltin').joinpath('preseed-files'))
        self.temp_dir = tempfile.gettempdir()
        self.http_directory = path.join(self.temp_dir, f"kroltin-preseed_{self.timestamp}")
        if not path.exists(self.http_directory):
            pathlib.Path(self.http_directory).mkdir(parents=True, exist_ok=True)

        # Log resoved paths
        self.logger.debug(f"scripts_dir:      {self.scripts_dir}")
        self.logger.debug(f"golden_images_dir:{self.golden_images_dir}")
        self.logger.debug(f"preseed_dir:      {self.preseed_dir}")
        self.logger.debug(f"temp_dir:         {self.temp_dir}")
        self.logger.debug(f"http_directory:   {self.http_directory}")

    # ----------------------------------------------------------------------
    # VM Build Methods
    # ----------------------------------------------------------------------

    def golden(
        self,
        packer_template: str,
        vm_name: str,
        vm_type: str,
        isos: list,
        cpus: int,
        memory: int,
        disk_size: int,
        ssh_username: str,
        ssh_password: str,
        iso_checksum: str,
        scripts: list,
        preseed_file: str,
        headless: bool,
        guest_os_type: str,
        vmware_version: int,
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

        resolved_template = self._resolve_packer_template(packer_template)
        if not self.init_template(resolved_template):
            self.logger.error(f"Packer init failed for template: {resolved_template}")
            return False

        self._fill_pressed(
            preseed_file=self._resolve_file_path(
                preseed_file,
                self.preseed_dir
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
            f"export_path={self._export_file_path(vm_name, vm_type)}",
            f"build_path={self._build_path(vm_name)}",
            f"headless={'true' if headless else 'false'}",
            f"guest_os_type={guest_os_type}",
            f"vmware_version={vmware_version}",
            f"source_vmx_path={self._source_vmx_path(vm_name)}"
        ]

        cmd = self._build_packer_cmd(packer_varables, resolved_template)
        try:
            if self._run_packer(cmd):
                self._remove_filled_preseed()
                self._remove_build_path(vm_name)
                self._get_build_hash(
                    vm_name,
                    self._map_extension(vm_type),
                    self._export_file_path(vm_name, vm_type)
                )
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
        ssh_username: str,
        ssh_password: str,
        scripts: list,
        export_path: str,
        headless: bool,
        export_file_type: str,
        ) -> bool:
        """Configure an existing VM golden image using Packer."""
        self.logger.debug(
            "Starting VM configure: %s, vm_name: %s, vm_type: %s, scripts: %s, "
            "export_path: %s",
            vm_file, vm_name, vm_type, str(scripts), export_path
        )

        resolved_template = self._resolve_packer_template(packer_template)
        if not self.init_template(resolved_template):
            self.logger.error(f"Packer init failed for template: {resolved_template}")
            return False

        packer_varables = [
            f"name={vm_name}",
            f"vm_file={self._find_vm(vm_file, vm_type)}",
            f"vm_type=[\"{self._map_sources(vm_type, build='configure')}\"]",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"scripts=[{self._quote_list(self._resolve_scripts(scripts))}]",
            f"export_path={export_path}",
            f"build_path={self._build_path(vm_name)}",
            f"headless={'true' if headless else 'false'}",
            f"export_file_type={export_file_type}"
        ]
        
        cmd = self._build_packer_cmd(packer_varables, resolved_template)

        try:
            if self._run_packer(cmd):
                self._remove_build_path(vm_name)
                self._get_build_hash(
                    vm_name,
                    self._map_extension(vm_type),
                    export_path
                )
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
        returncode, stdout, stderr = self.cmd_runner.run_command_stream(cmd)
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
    
    def _map_extension(self, vm_type: str) -> str:
        mapping = {
            "vmware": "vmx",
            "virtualbox": "ova",
            "hyperv": "vmcx",
        }
        if vm_type.lower() not in mapping:
            raise ValueError(f"Unsupported type '{vm_type}' for VM file extension mapping")
        return mapping.get(vm_type.lower(), vm_type)
    
    def _get_build_hash(self, vm_name: str, vm_file_extension: str, export_path: str) -> str:
        """Set the instance variables for MD5, SHA1, and SHA256 hashes from the .kroltin_build temporary directory"""
        if vm_file_extension == "vmx":
            vm_path = path.join(export_path, f"{vm_name}.{vm_file_extension}")
        elif vm_file_extension == "ova":
            vm_path = f"{export_path}.{vm_file_extension}"

        self.md5_hash = self._compute_file_hash(vm_path, algorithm='md5')
        self.sha1_hash = self._compute_file_hash(vm_path, algorithm='sha1')
        self.sha256_hash = self._compute_file_hash(vm_path, algorithm='sha256')

        self.logger.debug(f"Computed hashes for {vm_path} - MD5: {self.md5_hash}, SHA1: {self.sha1_hash}, SHA256: {self.sha256_hash}")
        return True

    @staticmethod
    def _compute_file_hash(file_path, algorithm: str = 'sha256') -> str:
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
        self.logger.debug(f"Temporary build path for VM '{vm_name}': {path.join(self.temp_dir, vm_name)}")
        return path.join(self.temp_dir, vm_name)

    def _resolve_file_path(self, file_name: str, kroltin_dir: str,) -> str:
        """Return the absolute path, checking kroltin directoires first, then user path. Perfer files in kroltin_dir"""
        kroltin_path = path.join(kroltin_dir, path.basename(file_name))
        if path.isfile(kroltin_path):
            return kroltin_path
        
        user_path = path.join(pathlib.Path(file_name), path.basename(file_name))
        if path.isfile(user_path):
            return user_path
        
        self.logger.warning(f"File '{file_name}' not found in kroltin directories or at user path.")
        return False
    
    def _resolve_dir_path(self, target_dir: str, kroltin_dir: str,) -> str:
        """Return the absolute path to directory, checking kroltin directoires first, then user path. Perfer files in kroltin_dir"""
        kroltin_path = path.join(kroltin_dir, path.basename(target_dir))
        if path.isdir(kroltin_path):
            return kroltin_path
        
        user_path = path.join(pathlib.Path(target_dir), path.basename(target_dir))
        if path.isdir(user_path):
            return user_path
        
        self.logger.warning(f"Directory '{target_dir}' not found in kroltin directories or at user path.")
        return False

    def _resolve_file(self, file_name: str, search_dir: str) -> str:
        """Return the absolute path to file name in search_dir, else check user path, else None."""
        file_in_dir = path.join(search_dir, path.basename(file_name))
        if path.isfile(file_in_dir):
            return file_in_dir
        elif path.isfile(file_name):
            return path.abspath(file_name)
        return None
    
    def _find_vm(self, vm_file: str, vm_type: str) -> str:
        """Return the VM file path for a given VM builder type"""
        if vm_type == "vmware":
            return self._find_vmx_in_dir(self._resolve_dir_path(vm_file, self.golden_images_dir))
                    
        return self._resolve_file_path(vm_file, self.golden_images_dir)

    def _find_vmx_in_dir(self, directory: str) -> str:
        """Recursively search for the first .vmx file in a directory."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.vmx'):
                    return path.join(root, file)
        self.logger.error(f"No .vmx file found in directory: {directory}")
        raise FileNotFoundError(f"No .vmx file found in directory: {directory}")

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

    def _export_file_path(self, vm_name: str, vm_type: str) -> str:
        """Return the full export file path with timestamp for a VM."""
        if vm_type == "vmware":
            return path.join(self.golden_images_dir, vm_name, vm_name)
        
        return path.join(self.golden_images_dir, vm_name)
    
    def _source_vmx_path(self, vm_name: str) -> str:
        """Return the full path to the VMX file for a given VM name."""
        source_vmx_path = path.join(self._build_path(vm_name), f"{vm_name}.vmx")
        self.logger.debug(f"Source VMX Path: {source_vmx_path}")
        return source_vmx_path

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
        """Remove the filled preseed file and its containing directory."""
        try:
            remove(self.filled_preseed_path)
            self.logger.debug(f"Removed filled preseed file: {self.filled_preseed_path}")
        except Exception as e:
            self.logger.error(f"Error removing filled preseed file: {e}")

        try:
            dirpath = path.dirname(self.filled_preseed_path)
            shutil.rmtree(dirpath)
            self.logger.debug(f"Removed preseed http directory: {dirpath}")
        except Exception as e:
            self.logger.error(f"Error removing preseed http directory: {e}")

    def _remove_build_path(self, vm_name: str):
        """Remove the temporary build path if it exists."""
        build_path = self._build_path(vm_name)
        if path.exists(build_path):
            try:
                shutil.rmtree(build_path)
                self.logger.debug(f"Removed build path: {build_path}")
            except Exception as e:
                self.logger.error(f"Error removing build path: {e}")