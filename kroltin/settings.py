
from os import path, listdir, remove
from shutil import copy2
import importlib.resources as resources
import logging

from kroltin.packer import Packer

# ANSI Colors
RED="\033[91m"
RESET="\033[0m"


class KroltinSettings:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scripts_dir = str(resources.files('kroltin') / 'scripts')
        self.packer_dir = str(resources.files('kroltin') / 'packer_templates')
        self.golden_images_dir = str(resources.files('kroltin') / 'golden_images')

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
        self._get_scripts()
        self.logger.info(f"Scripts: {', '.join(self.scripts_list)}")

    def list_packer_templates(self) -> None:
        """Print a list of all packer templates in the packer_templates directory."""
        self._get_packer_templates()
        self.logger.info(f"Templates: {', '.join(self.packer_templates)}")

    def list_golden_images(self) -> None:
        """Print a list of all builds in the golden_images directory."""
        builds = [f for f in listdir(self.golden_images_dir) if not f.startswith('.')]
        if builds:
            self.logger.info(f"Golden Images: {', '.join(builds)}")
        else:
            self.logger.info("No builds found in golden_images directory.")

    def list_all(self):
        """Print all packer templates, script files, and golden images."""
        self.list_packer_templates()
        self.list_scripts()
        self.list_golden_images()

    def _get_scripts(self):
        """Populate self.scripts_list with all .sh files in scripts directory."""
        self.scripts_list = []
        for file in listdir(self.scripts_dir):
            if file.endswith('.sh'):
                self.scripts_list.append(file)
        return True

    def _get_packer_templates(self):
        """Populate self.packer_templates with all .hcl and .json files in packer_templates directory."""
        self.packer_templates = []
        for file in listdir(self.packer_dir):
            if file.endswith('.hcl') or file.endswith('.json'):
                self.packer_templates.append(file)
        return True

    # ----------------------------------------------------------------------
    # Update Methods
    # ----------------------------------------------------------------------

    def add_script(self, script_path):
        """Add a script file to the scripts directory."""
        if not path.isfile(script_path):
            self.logger.error(f"Script file not found: {script_path}")
            return False
        if not script_path.endswith('.sh'):
            self.logger.error(f"Script file must have a .sh extension: {script_path}")
            return False
        dest = path.join(self.scripts_dir, path.basename(script_path))
        try:
            copy2(script_path, dest)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add script: {e}")
            return False

    def remove_script(self, script_name):
        """Remove a script file from the scripts directory."""
        script_path = path.join(self.scripts_dir, script_name)
        if not path.isfile(script_path):
            self.logger.error(f"Script file not found: {script_path}")
            return False
        try:
            remove(script_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove script: {e}")
            return False

    def add_packer_template(self, packer_template_path):
        """Add a packer template to the packer_templates directory."""
        if not path.isfile(packer_template_path):
            self.logger.error(f"Packer template not found: {packer_template_path}")
            return False
        if not (packer_template_path.endswith('.hcl') or packer_template_path.endswith('.json')):
            self.logger.error(f"Packer template must have a .hcl or .json extension: {packer_template_path}")
            return False
        dest = path.join(self.packer_dir, path.basename(packer_template_path))
        try:
            copy2(packer_template_path, dest)
        except Exception as e:
            self.logger.error(f"Failed to add packer template: {e}")
            return False
        
        # Run packer init and validate after adding
        packer = Packer()
        if packer.init_template(dest) and packer.validate_template(dest):
            return True
        else:
            self.logger.debug(f"Packer Init: {packer.init_template(dest)}")
            self.logger.debug(f"Packer Validate: {packer.validate_template(dest)}")

            self.remove_packer_template(dest)
            self.logger.debug("Packer template failed init/validate after adding. Template removed.")
            return False

    def remove_packer_template(self, packer_template_name):
        """Remove a packer template from the packer_templates directory."""
        packer_template_path = path.join(self.packer_dir, packer_template_name)
        if not path.isfile(packer_template_path):
            self.logger.error(f"Packer template not found: {packer_template_path}")
            return False
        try:
            remove(packer_template_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove packer template: {e}")
            return False
        

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

    def export_golden_image(self, image_name, dest_path):
        """Copy a golden image from golden_images to the given destination path."""
        src_path = path.join(self.golden_images_dir, image_name)
        if not path.exists(src_path):
            self.logger.error(f"Golden image not found: {src_path}")
            return False
        try:
            copy2(src_path, dest_path)
            self.logger.info(f"Golden image '{image_name}' exported to '{dest_path}'.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export golden image: {e}")
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

