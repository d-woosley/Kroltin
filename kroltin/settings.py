
import os
from os import path, listdir
from shutil import copy2
import importlib.resources as resources
import logging


class KroltinSettings:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scripts_dir = str(resources.files('kroltin') / 'scripts')
        self.packer_dir = str(resources.files('kroltin') / 'packer_templates')

    # ----------------------------------------------------------------------
    # List Methods
    # ----------------------------------------------------------------------

    def list_scripts(self):
        """Print a list of all script files in the scripts directory."""
        self._get_scripts()
        print("Scripts:")
        for file in self.scripts_list:
            print(f"  - {file}")

    def list_packer_templates(self):
        """Print a list of all packer templates in the packer_templates directory."""
        self._get_packer_templates()
        print("Packer Templates:")
        for template in self.packer_templates:
            print(f"  - {template}")

    def list_all(self):
        """Print all packer templates and script files."""
        self.list_packer_templates()
        self.list_scripts()

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
            os.remove(script_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove script: {e}")
            return False

    def add_packer_template(self, packer_template_path):
        """Add a packer template to the packer_templates directory."""
        if not path.isfile(packer_template_path):
            self.logger.error(f"Packer template not found: {packer_template_path}")
            return False
        dest = path.join(self.packer_dir, path.basename(packer_template_path))
        try:
            copy2(packer_template_path, dest)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add packer template: {e}")
            return False

    def remove_packer_template(self, packer_template_name):
        """Remove a packer template from the packer_templates directory."""
        packer_template_path = path.join(self.packer_dir, packer_template_name)
        if not path.isfile(packer_template_path):
            self.logger.error(f"Packer template not found: {packer_template_path}")
            return False
        try:
            os.remove(packer_template_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove packer template: {e}")
            return False

