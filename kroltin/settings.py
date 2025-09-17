
from os import path, listdir, remove, getcwd
from shutil import copy2
import importlib.resources as resources
import logging
import pathlib

from kroltin.packer import Packer


# ANSI Colors
RED="\033[91m"
RESET="\033[0m"


class KroltinSettings:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scripts_dir = resources.files('kroltin') / 'scripts'
        self.packer_dir = resources.files('kroltin') / 'packer_templates'
        self.golden_images_dir = resources.files('kroltin') / 'golden_images'
        self.preseed_dir = resources.files('kroltin') / 'preseed-files'

        self._ensure_directory(dir=self.golden_images_dir)

    # ----------------------------------------------------------------------
    # Check Methods
    # ----------------------------------------------------------------------

    def check_script_exists(self, script_name):
        """Check if a script exists in the scripts directory."""
        script_path = path.join(self.scripts_dir, script_name)
        return path.isfile(script_path)

    def check_packer_template_exists(self, template_name):
        """Check if a packer template exists in the packer_templates directory."""
        template_path = path.join(self.packer_dir, template_name)
        return path.isfile(template_path)

    # ----------------------------------------------------------------------
    # List Methods
    # ----------------------------------------------------------------------

    def list_scripts(self) -> None:
        """Print a list of all script files in the scripts directory."""
        scripts_list = self._get_files(self.scripts_dir, exts=['.sh'])
        self.logger.info(f"Scripts: {', '.join(scripts_list)}")

    def list_packer_templates(self) -> None:
        """Print a list of all packer templates in the packer_templates directory."""
        packer_templates = self._get_files(self.packer_dir, exts=['.hcl', '.json'])
        self.logger.info(f"Templates: {', '.join(packer_templates)}")

    def list_golden_images(self) -> None:
        """Print a list of all builds in the golden_images directory."""
        golden_images = self._get_files(self.golden_images_dir, exclude_dotfiles=True)
        if golden_images:
            self.logger.info(f"Golden Images: {', '.join(golden_images)}")
        else:
            self.logger.info("No builds found in golden_images directory.")

    def list_preseed_files(self) -> None:
        """Print a list of all preseed files in the preseed-files directory."""
        preseed_files = self._get_files(self.preseed_dir, exts=['.cfg', '.seed'])
        self.logger.info(f"Preseed Files: {', '.join(preseed_files)}")

    def list_all(self):
        """Print all packer templates, script files, and golden images."""
        self.list_packer_templates()
        self.list_scripts()
        self.list_golden_images()
        self.list_preseed_files()

    # ----------------------------------------------------------------------
    # Update Methods
    # ----------------------------------------------------------------------

    def add_script(self, script_path):
        """Add a script file to the scripts directory."""
        result = self._add_file(script_path, self.scripts_dir, ['.sh'], 'Script')
        return bool(result)

    def remove_script(self, script_name):
        """Remove a script file from the scripts directory."""
        return self._remove_file(script_name, self.scripts_dir, 'Script')

    def add_packer_template(self, packer_template_path):
        """Add a packer template to the packer_templates directory."""
        dest = self._add_file(packer_template_path, self.packer_dir, ['.hcl', '.json'], 'Packer template')
        if not dest:
            return False
        
        # Run packer init and validate after adding
        if not self._check_packer_template(dest):
            return False
        
        return True

    def remove_packer_template(self, packer_template_name):
        """Remove a packer template from the packer_templates directory."""
        return self._remove_file(packer_template_name, self.packer_dir, 'Packer template')
        
    def add_preseed_file(self, preseed_file_path):
        """Add a preseed file to the preseed-files directory."""
        result = self._add_file(preseed_file_path, self.preseed_dir, ['.cfg', '.seed'], 'Preseed')
        return bool(result)
    
    def remove_preseed_file(self, preseed_file_name):
        """Remove a preseed file from the preseed-files directory."""
        return self._remove_file(preseed_file_name, self.preseed_dir, 'Preseed')
        
    def remove_golden_image(self, image_name):
        """Remove a golden image from the golden_images directory after confirmation."""
        image_path = path.join(self.golden_images_dir, image_name)
        if not path.exists(image_path):
            self.logger.error(f"Golden image not found: {image_path}")
            return False
        
        self.logger.warning(f"{RED}WARNING: You are about to permanently delete '{image_name}' from golden_images. This action cannot be undone!{RESET}")
        if not self._confirm_action():
            self.logger.info("Aborted removal of golden image.")
            return False
        
        try:
            remove(image_path)
            self.logger.info(f"Golden image '{image_name}' removed.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove golden image: {e}")
            return False

    # ----------------------------------------------------------------------
    # Import/Export Methods
    # ----------------------------------------------------------------------

    def export_golden_image(self, image_name, dest_path):
        """Copy a golden image from golden_images to the given destination path."""
        src_path = path.join(self.golden_images_dir, image_name)
        if not path.exists(src_path):
            self.logger.error(f"Golden image not found: {src_path}")
            return False
        try:
            copy2(src_path, dest_path)
            abs_dest_path = path.abspath(dest_path)
            self.logger.info(f"Golden image '{image_name}' exported to '{abs_dest_path}'.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export golden image: {e}")
            return False

    def import_golden_image(self, src_path):
        """Import a golden image VM from the given path into the golden_images directory."""
        self.logger.debug(f"Importing golden image from: {src_path}")
        if path.isabs(src_path):
            src = pathlib.Path(src_path)
        else:
            src = pathlib.Path(getcwd()) / src_path

        self.logger.debug(f"Resolved source path: {src}")
        src_name = src.name
        self.logger.debug(f"Source name: {src_name}")
        dest = self.golden_images_dir / src_name

        if not src.exists():
            self.logger.error(f"Golden image source not found: {src}")
            return False
        
        if dest.exists():
            self.logger.error(f"Golden image '{src_name}' already exists in golden_images.")
            return False
        
        try:
            if src.is_dir():
                self.logger.warning("Importing directories not supported.")
            else:
                copy2(str(src), str(dest))
            self.logger.info(f"Golden image '{src_name}' imported to golden_images.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import golden image: {e}")
            return False

    # ----------------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------------

    def _confirm_action(self, message: str = "") -> bool:
        """Display a y/N confirmation prompt. Returns True if 'y' is selected."""
        while True:
            if message:
                confirm = input(f"  [?] {message}. Are you sure you want to proceed? [y/N]: ").strip().lower()
            else:
                confirm = input(f"  [?] Are you sure you want to proceed? [y/N]: ").strip().lower()
            if confirm == 'y' or confirm == 'yes':
                return True
            elif confirm == 'n' or confirm == 'no':
                return False
            self.logger.error("Response not understood. Please enter 'y' or 'n'")

    def _ensure_directory(self, dir):
        """Ensure a directory exists, creating it if necessary."""
        dir_path = pathlib.Path(dir)
        if not dir_path.exists():
            self.logger.debug(f"Creating directory at: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

    def _get_files(self, directory, exts=None, exclude_dotfiles=False):
        """Helper to get files from a directory, optionally filtering by extensions and dotfiles."""
        files = []
        for file in listdir(directory):
            if exclude_dotfiles and file.startswith('.'):
                continue
            if exts:
                if any(file.endswith(ext) for ext in exts):
                    files.append(file)
            else:
                files.append(file)
        return files

    def _add_file(self, src_path, dest_dir, valid_exts, type_desc):
        """Helper to add a file to a directory with extension/type checks."""
        if not path.isfile(src_path):
            self.logger.error(f"{type_desc} file not found: {src_path}")
            return False
        if not any(src_path.endswith(ext) for ext in valid_exts):
            self.logger.error(f"{type_desc} file must have one of {valid_exts} extensions: {src_path}")
            return False
        dest = path.join(dest_dir, path.basename(src_path))
        try:
            copy2(src_path, dest)
            return dest
        except Exception as e:
            self.logger.error(f"Failed to add {type_desc} file: {e}")
            return False

    def _remove_file(self, file_name, dir_path, type_desc):
        """Helper to remove a file from a directory."""
        file_path = path.join(dir_path, file_name)
        if not path.isfile(file_path):
            self.logger.error(f"{type_desc} file not found: {file_path}")
            return False
        try:
            remove(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove {type_desc} file: {e}")
            return False
        
    def _check_packer_template(self, template_path):
        """Check if a packer template is valid by running packer init and validate."""
        packer = Packer()
        if packer.init_template(template_path) and packer.validate_template(template_path):
            return True
        else:
            self.logger.debug(f"Packer Init: {packer.init_template(template_path)}")
            self.logger.debug(f"Packer Validate: {packer.validate_template(template_path)}")
            self.remove_packer_template(path.basename(template_path))
            self.logger.debug("Packer template failed init/validate after adding. Template removed.")
            return False