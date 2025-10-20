import json
import logging
import importlib.resources as resources
from typing import Dict, Optional, List


class TemplateManager:
    """Manages build templates stored in templates.json."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates_file = resources.files('kroltin') / 'templates.json'
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load templates from the JSON file."""
        try:
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                return data.get('templates', {})
        except FileNotFoundError:
            self.logger.error(f"Templates file not found: {self.templates_file}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing templates JSON: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            return {}
    
    def list_templates(self) -> List[str]:
        """Return a list of available template names."""
        return list(self.templates.keys())
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a specific template by name.
        
        Args:
            template_name: The name/key of the template
            
        Returns:
            Dictionary containing template configuration, or None if not found
        """
        template = self.templates.get(template_name)
        if template is None:
            self.logger.error(f"Template '{template_name}' not found")
            return None
        return template
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists.
        
        Args:
            template_name: The name/key of the template
            
        Returns:
            True if template exists, False otherwise
        """
        return template_name in self.templates
    
    def get_template_type(self, template_name: str) -> Optional[str]:
        """Get the type of a template (golden or configure).
        
        Args:
            template_name: The name/key of the template
            
        Returns:
            'golden' or 'configure', or None if template not found
        """
        template = self.get_template(template_name)
        if template:
            return template.get('type')
        return None
    
    def print_templates(self) -> None:
        """Print formatted list of all templates with descriptions."""
        if not self.templates:
            self.logger.info("No templates available.")
            return
        
        self.logger.info("Available Templates:")
        for key, template in self.templates.items():
            name = template.get('name', key)
            description = template.get('description', 'No description')
            template_type = template.get('type', 'unknown')
            self.logger.info(f"  {key} ({template_type}): {name} - {description}")
