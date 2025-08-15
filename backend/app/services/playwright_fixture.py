"""
Playwright Fixture Generation Library

This module provides functionality to generate Playwright fixture scripts
using the fixture.template with Handlebars-like template rendering.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Import the TypeScript formatter
try:
    from ..utils.typescript_formatter import format_fixture_code
    FORMATTER_AVAILABLE = True
except ImportError:
    FORMATTER_AVAILABLE = False
    logger.warning("TypeScript formatter not available")

logger = logging.getLogger(__name__)


class PlaywrightFixtureGenerator:
    """Generator class for creating Playwright fixture files from templates."""
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the fixture generator.
        
        Args:
            template_dir: Directory containing template files.
                         If None, uses backend/template/
        """
        if template_dir is None:
            # Get the backend/template directory
            current_file = Path(__file__)
            backend_dir = current_file.parent.parent.parent  # Go up from services -> app -> backend
            self.template_dir = backend_dir / "template"
        else:
            self.template_dir = Path(template_dir)
        
        self.fixture_template_path = self.template_dir / "fixture.template"
        
        if not self.fixture_template_path.exists():
            logger.error(f"Fixture template not found: {self.fixture_template_path}")
            raise FileNotFoundError(f"Fixture template not found: {self.fixture_template_path}")
    
    def _load_template(self) -> str:
        """
        Load the fixture template content.
        
        Returns:
            Template content as string
        """
        try:
            with open(self.fixture_template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            raise
    
    def _clean_export_name(self, name: str) -> str:
        """
        Clean name to create a valid JavaScript export name.
        
        Args:
            name: Original name
            
        Returns:
            Cleaned export name (camelCase, valid JS identifier)
        """
        # Remove special characters and spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        
        # Convert to camelCase
        words = cleaned.split()
        if not words:
            return 'fixture'
        
        # First word lowercase, rest title case
        camel_case = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
        
        # Ensure it starts with a letter
        if not camel_case[0].isalpha():
            camel_case = 'fixture' + camel_case.capitalize()
        
        return camel_case
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render template with Handlebars-like syntax.
        
        Args:
            template: Template string
            context: Context variables for rendering
            
        Returns:
            Rendered template
        """
        rendered = template
        
        # Handle type conditionals first to select the right block
        if 'type' in context:
            type_value = context['type']
            
            if type_value == 'extend':
                # Extract only the extend block
                match = re.search(
                    r'{{\s*#if\s+\(eq\s+type\s+"extend"\)\s*}}(.*?){{\s*else\s+if\s+\(eq\s+type\s+"inline"\)\s*}}',
                    rendered,
                    flags=re.DOTALL
                )
                if match:
                    rendered = match.group(1)
            elif type_value == 'inline':
                # Extract only the inline block
                match = re.search(
                    r'{{\s*else\s+if\s+\(eq\s+type\s+"inline"\)\s*}}(.*?){{\s*else\s*}}',
                    rendered,
                    flags=re.DOTALL
                )
                if match:
                    rendered = match.group(1)
            else:
                # Extract else block (unsupported)
                match = re.search(
                    r'{{\s*else\s*}}(.*?){{\s*/if\s*}}',
                    rendered,
                    flags=re.DOTALL
                )
                if match:
                    rendered = match.group(1)
        
        # Handle {{#if description}} blocks
        if 'description' in context and context['description']:
            rendered = re.sub(
                r'{{\s*#if\s+description\s*}}(.*?){{\s*/if\s*}}',
                r'\1',
                rendered,
                flags=re.DOTALL
            )
        else:
            rendered = re.sub(
                r'{{\s*#if\s+description\s*}}.*?{{\s*/if\s*}}',
                '',
                rendered,
                flags=re.DOTALL
            )
        
        # Handle {{#if steps}} blocks
        steps = context.get('steps', [])
        if steps:
            # Handle {{#each steps}} loop first
            steps_content = ""
            for i, step in enumerate(steps):
                step_content = f"// Step {step.get('order', i+1)}: {step.get('action', 'Unknown')}\n"
                
                # Add Data line
                data = step.get('data', '')
                step_content += f"// Data: {data}\n"
                
                # Add Expected line
                expected = step.get('expected', '')
                step_content += f"// Expected: {expected}\n"
                
                # Add playwright script
                if step.get('playwright_script'):
                    step_content += f"{step['playwright_script']}\n"
                else:
                    step_content += f"// TODO: Implement step {step.get('order', i+1)}\n"
                
                # Add spacing between steps (except last one)
                if i < len(steps) - 1:
                    step_content += "\n"
                
                steps_content += step_content
            
            # Replace {{#each steps}}...{{/each}} with actual steps content
            rendered = re.sub(
                r'{{\s*#each\s+steps\s*}}.*?{{\s*/each\s*}}',
                steps_content,
                rendered,
                flags=re.DOTALL
            )
            
            # Keep the if block content
            rendered = re.sub(
                r'{{\s*#if\s+steps\s*}}(.*?){{\s*/if\s*}}',
                r'\1',
                rendered,
                flags=re.DOTALL
            )
        else:
            # Remove the entire if block if no steps
            rendered = re.sub(
                r'{{\s*#if\s+steps\s*}}.*?{{\s*/if\s*}}',
                '',
                rendered,
                flags=re.DOTALL
            )
        
        # Handle triple braces {{{content}}} - no HTML escaping needed for our use case
        for key, value in context.items():
            pattern = f'{{{{{{{key}}}}}}}'
            rendered = rendered.replace(pattern, str(value))
        
        # Handle simple variable substitution {{variable}}
        for key, value in context.items():
            pattern = f'{{{{{key}}}}}'
            rendered = rendered.replace(pattern, str(value))
        
        # Clean up any remaining template syntax
        rendered = re.sub(r'{{\s*[^}]+\s*}}', '', rendered)
        
        return rendered
    
    def generate_fixture(
        self,
        name: str,
        fixture_type: str,
        content: str,
        description: str = None,
        output_path: str = None,
        steps: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a Playwright fixture file.
        
        Args:
            name: Human-readable name of the fixture
            fixture_type: Type of fixture ('extend' or 'inline')
            content: JavaScript/TypeScript content for the fixture
            description: Optional description
            output_path: Optional custom output path. If None, generates filename from name
            steps: Optional list of steps to include in the fixture
            
        Returns:
            Dictionary with generation results
        """
        try:
            # Load template
            template = self._load_template()
            
            # Prepare context
            export_name = self._clean_export_name(name)
            
            context = {
                'name': name,
                'type': fixture_type,
                'content': content,
                'exportName': export_name,
                'description': description or '',
                'steps': steps or []
            }
            
            # Render template
            rendered_content = self._render_template(template, context)
            
            # Format the generated code with Prettier if available
            if FORMATTER_AVAILABLE:
                try:
                    formatted_content = format_fixture_code(rendered_content)
                    rendered_content = formatted_content
                    logger.debug("Applied TypeScript formatting to generated fixture")
                except Exception as e:
                    logger.warning(f"Failed to format generated fixture: {str(e)}")
            
            # Generate output filename if not provided
            if output_path is None:
                filename = f"{export_name}.fixture.ts"
                output_path = filename
            
            result = {
                'success': True,
                'content': rendered_content,
                'export_name': export_name,
                'filename': output_path,
                'template_context': context
            }
            
            logger.info(f"Generated fixture '{name}' -> {output_path}")
            return result
            
        except Exception as e:
            error_msg = f"Error generating fixture: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'content': None,
                'export_name': None,
                'filename': None
            }
    
    def save_fixture_to_project(
        self,
        project_name: str,
        fixture_result: Dict[str, Any],
        project_manager = None
    ) -> Dict[str, Any]:
        """
        Save generated fixture to a specific Playwright project.
        
        Args:
            project_name: Name of the Playwright project
            fixture_result: Result from generate_fixture()
            project_manager: Optional PlaywrightProjectManager instance
            
        Returns:
            Dictionary with save results
        """
        try:
            if not fixture_result.get('success'):
                return {
                    'success': False,
                    'error': 'Invalid fixture result provided'
                }
            
            # Import here to avoid circular imports
            if project_manager is None:
                from .playwright_project import playwright_manager
                project_manager = playwright_manager
            
            # Get project path
            project_path = project_manager.get_project_path(project_name)
            if not project_path:
                return {
                    'success': False,
                    'error': f"Project '{project_name}' not found"
                }
            
            # Create fixtures directory if it doesn't exist
            fixtures_dir = project_path / 'fixtures'
            fixtures_dir.mkdir(exist_ok=True)
            
            # Write fixture file
            fixture_file_path = fixtures_dir / fixture_result['filename']
            
            with open(fixture_file_path, 'w', encoding='utf-8') as f:
                f.write(fixture_result['content'])
            
            logger.info(f"Saved fixture to: {fixture_file_path}")
            
            return {
                'success': True,
                'file_path': str(fixture_file_path),
                'project_name': project_name,
                'fixture_name': fixture_result['export_name']
            }
            
        except Exception as e:
            error_msg = f"Error saving fixture to project: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def list_project_fixtures(self, project_name: str, project_manager = None) -> List[Dict[str, Any]]:
        """
        List all fixtures in a Playwright project.
        
        Args:
            project_name: Name of the Playwright project
            project_manager: Optional PlaywrightProjectManager instance
            
        Returns:
            List of fixture information dictionaries
        """
        try:
            # Import here to avoid circular imports
            if project_manager is None:
                from .playwright_project import playwright_manager
                project_manager = playwright_manager
            
            # Get project path
            project_path = project_manager.get_project_path(project_name)
            if not project_path:
                return []
            
            fixtures_dir = project_path / 'fixtures'
            if not fixtures_dir.exists():
                return []
            
            fixtures = []
            
            # Find all .fixture.ts files
            for fixture_file in fixtures_dir.glob('*.fixture.ts'):
                try:
                    # Read file to extract basic info
                    with open(fixture_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract export name and description from content
                    export_match = re.search(r'export\s+(?:const|function)\s+(\w+)', content)
                    export_name = export_match.group(1) if export_match else fixture_file.stem
                    
                    # Extract description from comments
                    desc_match = re.search(r'/\*\*\s*\n\s*\*\s*([^*\n]+)', content)
                    description = desc_match.group(1).strip() if desc_match else None
                    
                    fixtures.append({
                        'filename': fixture_file.name,
                        'export_name': export_name,
                        'description': description,
                        'file_path': str(fixture_file),
                        'size': fixture_file.stat().st_size
                    })
                    
                except Exception as e:
                    logger.warning(f"Error reading fixture file {fixture_file}: {str(e)}")
                    continue
            
            return sorted(fixtures, key=lambda x: x['filename'])
            
        except Exception as e:
            logger.error(f"Error listing project fixtures: {str(e)}")
            return []


# Global instance for easy access
fixture_generator = PlaywrightFixtureGenerator()


# Convenience functions
def create_fixture(
    name: str,
    fixture_type: str,
    content: str,
    description: str = None
) -> Dict[str, Any]:
    """
    Convenience function to create a fixture.
    
    Args:
        name: Human-readable name of the fixture
        fixture_type: Type of fixture ('extend' or 'inline')
        content: JavaScript/TypeScript content for the fixture
        description: Optional description
        
    Returns:
        Dictionary with generation results
    """
    return fixture_generator.generate_fixture(name, fixture_type, content, description)


def save_fixture(
    project_name: str,
    fixture_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to save fixture to project.
    
    Args:
        project_name: Name of the Playwright project
        fixture_result: Result from create_fixture()
        
    Returns:
        Dictionary with save results
    """
    return fixture_generator.save_fixture_to_project(project_name, fixture_result)


def list_fixtures(project_name: str) -> List[Dict[str, Any]]:
    """
    Convenience function to list project fixtures.
    
    Args:
        project_name: Name of the Playwright project
        
    Returns:
        List of fixture information dictionaries
    """
    return fixture_generator.list_project_fixtures(project_name)
