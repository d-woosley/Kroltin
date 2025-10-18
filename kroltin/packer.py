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
import crypt
import re


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
        self.templates_build_dir = path.join(self.temp_dir, f"kroltin-templates_{self.timestamp}")
        # Keep http_directory as alias for preseed files served over HTTP
        self.http_directory = self.templates_build_dir

        # Log resoved paths
        self.logger.debug(f"scripts_dir:        {self.scripts_dir}")
        self.logger.debug(f"golden_images_dir:  {self.golden_images_dir}")
        self.logger.debug(f"preseed_dir:        {self.preseed_dir}")
        self.logger.debug(f"temp_dir:           {self.temp_dir}")
        self.logger.debug(f"templates_build_dir:{self.templates_build_dir}")

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
        hostname: str,
        iso_checksum: str,
        scripts: list,
        preseed_file: str,
        headless: bool,
        guest_os_type: str,
        vmware_version: int,
        random_password: bool = False,
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
            hostname=hostname
        )

        # Resolve and check scripts for template variables
        resolved_scripts = self._resolve_scripts(scripts)
        filled_scripts = self._check_and_fill_scripts(
            resolved_scripts,
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            hostname=hostname
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
            f"scripts=[{self._quote_list(filled_scripts)}]",
            f"export_path={self._gold_export_path(vm_name, vm_type)}",
            f"build_path={self._build_path(vm_name)}",
            f"headless={'true' if headless else 'false'}",
            f"guest_os_type={guest_os_type}",
            f"vmware_version={vmware_version}",
            f"source_vmx_path={self._source_vmx_path(vm_name)}"
        ]

        cmd = self._build_packer_cmd(packer_varables, resolved_template)

        if self._run_packer(cmd):
            self._build_cleanup(vm_name=vm_name, ssh_password=ssh_password, random_password_used=random_password)
            return True
        else:
            self._build_cleanup(vm_name=vm_name, ssh_password=ssh_password, random_password_used=random_password)
            return False

    def configure(
        self,
        packer_template: str,
        vm_name: str,
        vm_type: str,
        vm_file: str,
        ssh_username: str,
        ssh_password: str,
        hostname: str,
        scripts: list,
        export_path: str,
        headless: bool,
        export_file_type: str,
        random_password: bool = False,
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

        # Resolve and check scripts for template variables
        resolved_scripts = self._resolve_scripts(scripts)
        filled_scripts = self._check_and_fill_scripts(
            resolved_scripts,
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            hostname=hostname
        )

        packer_varables = [
            f"name={vm_name}",
            f"vm_file={self._find_vm(vm_file, vm_type)}",
            f"vm_type=[\"{self._map_sources(vm_type, build='configure')}\"]",
            f"ssh_username={ssh_username}",
            f"ssh_password={ssh_password}",
            f"scripts=[{self._quote_list(filled_scripts)}]",
            f"export_path={self._config_export_path(vm_name, vm_type, export_path)}",
            f"build_path={self._build_path(vm_name)}",
            f"headless={'true' if headless else 'false'}",
            f"export_file_type={export_file_type}",
            f"source_vmx_path={self._source_vmx_path(vm_name)}"
        ]
        
        cmd = self._build_packer_cmd(packer_varables, resolved_template)

        if self._run_packer(cmd):
            self._build_cleanup(vm_name=vm_name, ssh_password=ssh_password, random_password_used=random_password)
            return True
        else:
            self._build_cleanup(vm_name=vm_name, ssh_password=ssh_password, random_password_used=random_password)
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
        self.logger.debug(f"Packer command returned code: {returncode}")
        if returncode is None:
            return False
        elif int(returncode) == 0:
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
    
    @staticmethod
    def _compute_file_hash(file_path, algorithm: str = 'sha256') -> str:
        """Compute the hash of a file using the specified algorithm."""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()

    def _build_cleanup(self, vm_name: str, ssh_password: str = None, random_password_used: bool = False):
        """Centralized cleanup for golden/configure flows.

        Removes the filled preseed, filled scripts, and temporary build path. 
        If a random password was used, print it to stdout (not to logs) so it 
        isn't stored in logging outputs.
        """
        try:
            # Remove templates build directory (contains filled preseed and scripts)
            try:
                if path.exists(self.templates_build_dir):
                    shutil.rmtree(self.templates_build_dir)
                    self.logger.debug(f"Removed templates build directory: {self.templates_build_dir}")
            except Exception as e:
                self.logger.error(f"Error removing templates build directory {self.templates_build_dir}: {e}")

            # Remove build path
            try:
                build_path = self._build_path(vm_name)
                if path.exists(build_path):
                    shutil.rmtree(build_path)
                    self.logger.debug(f"Removed build path: {build_path}")
            except Exception as e:
                self.logger.error(f"Error removing build path: {e}")

            # If a random password was used, print it to stdout (not in logs)
            if random_password_used and ssh_password:
                print(f"  ######## Random SSH password for '{vm_name}': {ssh_password} ########")
        except Exception:
            self.logger.debug("_build_cleanup encountered an unexpected error, continuing.")

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

    def _gold_export_path(self, vm_name: str, vm_type: str) -> str:
        """Return the full golden build export file path for a given VM type."""
        if vm_type == "vmware":
            return path.join(self.golden_images_dir, vm_name, vm_name)
        
        return path.join(self.golden_images_dir, vm_name)
    
    def _config_export_path(self, vm_name: str, vm_type: str, export_path: str) -> str:
        """
        Return the full configuration build export file path for a given VM type. 
        Create VMware VM directory if needed.
        """
        if vm_type == "vmware":
            if not path.isdir(export_path):
                os.makedirs(export_path, exist_ok=True)

            return path.join(export_path, path.basename(export_path))

        return export_path
    
    def _source_vmx_path(self, vm_name: str) -> str:
        """Return the full path to the VMX file for a given VM name."""
        return path.join(self._build_path(vm_name), f"{vm_name}.vmx") 

    def _remove_build_path(self, vm_name: str):
        """Remove the temporary build path if it exists."""
        build_path = self._build_path(vm_name)
        if path.exists(build_path):
            try:
                shutil.rmtree(build_path)
                self.logger.debug(f"Removed build path: {build_path}")
            except Exception as e:
                self.logger.error(f"Error removing build path: {e}")

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
            "export_path=dummy_export_path",
            "source_vmx_path=example-vmx-path.vmx"
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

    def _prompt_user_confirmation(self, message: str, default: bool = False) -> bool:
        """Prompt user for yes/no confirmation.
        
        Args:
            message: The question/message to display to the user
            default: Default response if user just presses Enter (False = No, True = Yes)
            
        Returns:
            True if user confirms (y/yes), False otherwise
        """
        prompt_suffix = "[Y/n]" if default else "[y/N]"
        response = input(f"  {message} {prompt_suffix}: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes']

    def _map_template_variables(self, **kwargs) -> dict:
        """Map Python variable names to their template placeholders.
        
        Args:
            **kwargs: Keyword arguments containing variable values
            
        Returns:
            Dictionary mapping template placeholders to their values
        """
        # Define the mapping from Python variables to template placeholders
        variable_mapping = {
            'ssh_username': '{{USERNAME}}',
            'hostname': '{{HOSTNAME}}',
        }
        
        # Build the template variable map
        template_map = {}
        
        for py_var, placeholder in variable_mapping.items():
            value = kwargs.get(py_var)
            if value is not None:
                template_map[placeholder] = value
        
        # Handle special case: PASSWORD_CRYPT derived from ssh_password
        if 'ssh_password' in kwargs and kwargs['ssh_password'] is not None:
            password_crypt = self._generate_sha512_crypt(kwargs['ssh_password'])
            template_map['{{PASSWORD_CRYPT}}'] = password_crypt
        
        return template_map

    def _find_template_variables_in_file(self, file_path: str) -> set:
        """Find all template variables ({{VAR}}) in a file.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Set of template variable placeholders found in the file
        """
        variables = set()
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Find all {{VARIABLE}} patterns
                matches = re.findall(r'\{\{([A-Z_]+)\}\}', content)
                variables = {f'{{{{{var}}}}}' for var in matches}
        except Exception as e:
            self.logger.error(f"Error scanning file for template variables: {e}")
            
        return variables

    def _check_and_fill_scripts(self, script_paths: list, **kwargs) -> list:
        """Check bash scripts for template variables and fill them if needed.
        
        Scans each script for template variables. If variables are found:
        - If all required variables are provided, create filled versions
        - If variables are missing, warn user and prompt to proceed
        
        Args:
            script_paths: List of absolute paths to script files
            **kwargs: Variable name/value pairs available for substitution
            
        Returns:
            List of script paths (filled versions if variables were found, originals otherwise)
        """
        filled_scripts = []
        
        for script_path in script_paths:
            # Find template variables in the script
            found_vars = self._find_template_variables_in_file(script_path)
            
            if not found_vars:
                # No variables found, use original script
                filled_scripts.append(script_path)
                continue
            
            # Check which variables we can fill
            available_map = self._map_template_variables(**kwargs)
            missing_vars = found_vars - set(available_map.keys())
            
            if missing_vars:
                # Some variables are missing
                self.logger.warning(
                    f"Script '{path.basename(script_path)}' contains template variables "
                    f"that were not provided: {', '.join(sorted(missing_vars))}"
                )
                
                message = (
                    f"Script '{path.basename(script_path)}' has unfilled variables: {', '.join(sorted(missing_vars))}.\n"
                    f"  Do you want to proceed with this script anyway?"
                )
                
                if not self._prompt_user_confirmation(message, default=False):
                    self.logger.error(f"User declined to proceed with script: {script_path}")
                    raise ValueError(f"Script '{path.basename(script_path)}' has missing required variables")
            
            # Create filled version of the script in templates_build_dir
            script_basename = path.basename(script_path)
            filled_script_name = f"filled_{self.timestamp}_{script_basename}"
            filled_script_path = path.join(self.templates_build_dir, filled_script_name)
            
            # Ensure the templates_build_dir exists
            if not path.exists(self.templates_build_dir):
                pathlib.Path(self.templates_build_dir).mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Filling template variables in script: {script_basename}")
            self._fill_template_variables(
                input_file=script_path,
                output_file=filled_script_path,
                **kwargs
            )
            
            filled_scripts.append(filled_script_path)
        
        return filled_scripts

    def _fill_template_variables(self,
            input_file: str,
            output_file: str,
            **kwargs
        ) -> bool:
        """Fill in template variables in a file with the provided values.
        
        Args:
            input_file: Path to the template file to read
            output_file: Path to the output file to write
            **kwargs: Variable name/value pairs (e.g., ssh_username='user', hostname='myhost')
            
        Returns:
            True if successful, raises exception otherwise
        """
        # Get the variable mapping
        variable_map = self._map_template_variables(**kwargs)
        
        try:
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                for line in infile:
                    # Replace all variables in the line
                    for placeholder, value in variable_map.items():
                        line = line.replace(placeholder, value)
                    outfile.write(line)
            
            self.logger.debug(f"Filled template file created at: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error filling template file: {e}")
            raise e

    def _fill_pressed(self,
            preseed_file: str,
            ssh_username: str,
            ssh_password: str,
            hostname: str
        ) -> str:
        """Fill in the preseed file with the provided SSH username and password."""
        if not path.exists(self.templates_build_dir):
            pathlib.Path(self.templates_build_dir).mkdir(parents=True, exist_ok=True)

        self.filled_preseed_name = f"filled_{self.timestamp}_{path.basename(preseed_file)}"
        self.filled_preseed_path = path.join(
            self.templates_build_dir, 
            self.filled_preseed_name
        )
        
        # Use the new template filling function
        self._fill_template_variables(
            input_file=preseed_file,
            output_file=self.filled_preseed_path,
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            hostname=hostname
        )
        
        self.logger.info(f"Filled preseed file created at: {self.filled_preseed_path}")
        return True
        
    def _remove_filled_preseed(self):
        """Remove the filled preseed file and its containing directory."""
        try:
            remove(self.filled_preseed_path)
            self.logger.debug(f"Removed filled preseed file: {self.filled_preseed_path}")
        except Exception as e:
            self.logger.error(f"Error removing filled preseed file: {e}")

    def _generate_sha512_crypt(self, password: str) -> str:
        """Generate a SHA-512 crypt(6) hash for the given password."""
        try:
            salt = crypt.mksalt(crypt.METHOD_SHA512)
            return crypt.crypt(password, salt)
        except Exception as e:
            self.logger.error(f"Failed to generate SHA-512 crypt hash via crypt module: {e}")
            raise