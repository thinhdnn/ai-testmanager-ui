"""
Playwright Test Case Generation Library

This module provides functionality to generate Playwright test scripts
using the test.template with Handlebars-like template rendering.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Import the TypeScript formatter
try:
    from ..utils.typescript_formatter import format_test_case_code
    FORMATTER_AVAILABLE = True
except ImportError:
    FORMATTER_AVAILABLE = False
    logger.warning("TypeScript formatter not available")

try:
    from sqlalchemy.orm import Session
except ImportError:
    logger.warning("SQLAlchemy not available")
    Session = Any  # type: ignore

from ..models.test_case import TestCase
from ..models.step import Step
from ..models.fixture import Fixture
from ..crud.test_case import get_test_case, get_test_case_fixtures
from ..crud.step import get_steps_by_test_case


class PlaywrightTestCaseGenerator:
    """Generator class for creating Playwright test case files from templates."""
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the test case generator.
        
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
        
        self.test_template_path = self.template_dir / "test.template"
        
        if not self.test_template_path.exists():
            logger.error(f"Test template not found: {self.test_template_path}")
            raise FileNotFoundError(f"Test template not found: {self.test_template_path}")
    
    def _load_template(self) -> str:
        """
        Load the test template content.
        
        Returns:
            Template content as string
        """
        try:
            with open(self.test_template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            raise
    
    def _clean_test_name(self, name: str) -> str:
        """
        Clean test case name for use in test files.
        
        Args:
            name: Original test case name
            
        Returns:
            Cleaned test name
        """
        # Remove special characters but keep spaces for readability
        cleaned = re.sub(r'[^\w\s-]', '', name)
        return cleaned.strip()
    
    def _parse_tags(self, tags_string: str) -> List[str]:
        """
        Parse tags string into list of tags.
        
        Args:
            tags_string: Comma-separated tags string
            
        Returns:
            List of tag names
        """
        if not tags_string:
            return []
        
        tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        return tags
    

    
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
        
        # Handle simple variable substitution first
        for key, value in context.items():
            if key not in ['steps', 'fixtures', 'tags']:
                pattern = f'{{{{{key}}}}}'
                rendered = rendered.replace(pattern, str(value))
        
        # Handle tags conditional and loop
        tags = context.get('tags', [])
        if tags:
            # Build tag list first
            tags_content = ""
            for i, tag in enumerate(tags):
                tag_item = f"'@{tag}'"
                if i < len(tags) - 1:
                    tag_item += ", "
                tags_content += tag_item
            
            # Replace {{#each tags}} with tag list
            rendered = re.sub(
                r'{{\s*#each\s+tags\s*}}.*?{{\s*/each\s*}}',
                tags_content,
                rendered,
                flags=re.DOTALL
            )
            
            # Keep the if block (with tags), remove else block and closing if
            rendered = re.sub(
                r'{{\s*#if\s+tags\s*}}(.*?){{\s*else\s*}}.*?{{\s*/if\s*}}',
                r'\1',
                rendered,
                flags=re.DOTALL
            )
            
            # Remove any remaining {{/if}} that might be orphaned
            rendered = re.sub(r'{{\s*/if\s*}}', '', rendered)
        else:
            # Keep the else block (no tags), remove if block and closing if
            rendered = re.sub(
                r'{{\s*#if\s+tags\s*}}.*?{{\s*else\s*}}(.*?){{\s*/if\s*}}',
                r'\1',
                rendered,
                flags=re.DOTALL
            )
            
            # Remove any remaining {{/if}} that might be orphaned
            rendered = re.sub(r'{{\s*/if\s*}}', '', rendered)
        
        # Handle fixture-related logic
        fixtures = context.get('fixtures', [])
        has_extend_fixtures = any(f.get('mode') == 'extend' for f in fixtures)
        
        # Build fixture parameters for function signature
        fixture_params = []
        if has_extend_fixtures:
            for fixture in fixtures:
                if fixture.get('mode') == 'extend':
                    fixture_params.append(fixture.get('exportName', 'fixture'))
        
        fixture_param_str = ', ' + ', '.join(fixture_params) if fixture_params else ''
        
        # Handle {{#if (any fixtures "mode" "extend")}} conditionals
        if has_extend_fixtures:
            # Keep the extend fixture blocks
            rendered = re.sub(
                r'{{\s*#if\s+\(any\s+fixtures\s+"mode"\s+"extend"\)\s*}}(.*?){{\s*else\s*}}.*?{{\s*/if\s*}}',
                lambda m: m.group(1).replace('{ page }', f'{{ page{fixture_param_str} }}'),
                rendered,
                flags=re.DOTALL
            )
        else:
            # Keep the else block (no extend fixtures)
            rendered = re.sub(
                r'{{\s*#if\s+\(any\s+fixtures\s+"mode"\s+"extend"\)\s*}}.*?{{\s*else\s*}}(.*?){{\s*/if\s*}}',
                r'\1',
                rendered,
                flags=re.DOTALL
            )
        
        # Handle {{#each fixtures}} loops for individual fixture conditionals
        for fixture in fixtures:
            if fixture.get('mode') == 'extend':
                # Replace {{#if (eq mode "extend")}} with fixture export name
                pattern = r'{{\s*#if\s+\(eq\s+mode\s+"extend"\)\s*}}\s*,\s*([^}]+){{\s*/if\s*}}'
                replacement = f', {fixture.get("exportName", "fixture")}'
                rendered = re.sub(pattern, replacement, rendered)
        
        # Handle {{#each steps}} loop
        steps = context.get('steps', [])
        steps_content = ""
        
        for i, step in enumerate(steps):
            step_number = i + 1
            step_content = f"  // Step {step_number}: {step.get('action', 'Unknown action')}\n"
            
            if step.get('disabled', False):
                step_content += "  /* DISABLED STEP\n"
                if step.get('playwrightCode'):
                    step_content += f"  {step.get('playwrightCode')}\n"
                if step.get('expected'):
                    step_content += f"  // Expected: {step.get('expected')}\n"
                step_content += "  */\n"
            else:
                if step.get('playwrightCode'):
                    step_content += f"  {step.get('playwrightCode')}\n"
                else:
                    step_content += "  // TODO: Implement this step\n"
                if step.get('expected'):
                    step_content += f"  // Expected: {step.get('expected')}\n"
            
            if i < len(steps) - 1:
                step_content += "\n"
            
            steps_content += step_content
        
        # Replace the steps loop
        rendered = re.sub(
            r'{{\s*#each\s+steps\s*}}.*?{{\s*/each\s*}}',
            steps_content,
            rendered,
            flags=re.DOTALL
        )
        
        # Clean up any remaining template syntax and extra whitespace
        rendered = re.sub(r'{{\s*[^}]+\s*}}', '', rendered)
        rendered = re.sub(r'\n\s*\n\s*\n', '\n\n', rendered)  # Remove excessive blank lines
        
        # Clean up extra commas and spaces in function parameters
        rendered = re.sub(r',\s*}\)', '})', rendered)
        rendered = re.sub(r'{\s*page\s*}\)', '{ page })', rendered)
        
        return rendered
    
    def generate_test_case(
        self,
        db: Session,
        test_case_id: str,
        project_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate a Playwright test case file from database test case.
        
        Args:
            db: Database session
            test_case_id: Test case ID
            project_name: Optional project name for context
            
        Returns:
            Dictionary with generation results
        """
        try:
            # Get test case from database
            test_case = get_test_case(db, test_case_id)
            if not test_case:
                return {
                    'success': False,
                    'error': f'Test case not found: {test_case_id}'
                }
            
            # Get test case steps
            steps = get_steps_by_test_case(db, test_case_id)
            
            # Get test case fixtures
            fixtures_data = get_test_case_fixtures(db, test_case_id)
            
            # Load template
            template = self._load_template()
            
            # Prepare context
            test_name = self._clean_test_name(test_case.name)
            tags = self._parse_tags(test_case.tags) if test_case.tags else []
            
            # Convert steps to template format
            template_steps = []
            for step in steps:
                template_steps.append({
                    'action': step.action,
                    'playwrightCode': step.playwright_script or '',
                    'expected': step.expected or '',
                    'disabled': step.disabled,
                    'data': step.data
                })
            
            # Convert fixtures to template format
            template_fixtures = []
            for fixture_data in fixtures_data:
                # Determine fixture mode based on type
                mode = 'extend' if fixture_data['type'] == 'extend' else 'inline'
                
                # Generate export name from fixture name
                export_name = self._clean_export_name(fixture_data['name'])
                
                template_fixtures.append({
                    'name': fixture_data['name'],
                    'mode': mode,
                    'exportName': export_name,
                    'type': fixture_data['type']
                })
            
            context = {
                'testCaseName': test_name,
                'tags': tags,
                'steps': template_steps,
                'fixtures': template_fixtures,
                'projectName': project_name or 'default'
            }
            
            # Render template
            rendered_content = self._render_template(template, context)
            
            # Format the generated code with Prettier if available
            if FORMATTER_AVAILABLE:
                try:
                    formatted_content = format_test_case_code(rendered_content)
                    rendered_content = formatted_content
                    logger.debug("Applied TypeScript formatting to generated test case")
                except Exception as e:
                    logger.warning(f"Failed to format generated test case: {str(e)}")
            
            # Generate output filename
            safe_name = re.sub(r'[^\w\s-]', '', test_name).replace(' ', '-').lower()
            filename = f"{safe_name}.spec.ts"
            
            result = {
                'success': True,
                'content': rendered_content,
                'filename': filename,
                'test_case_name': test_name,
                'test_case_id': test_case_id,
                'template_context': context
            }
            
            logger.info(f"Generated test case '{test_name}' -> {filename}")
            return result
            
        except Exception as e:
            error_msg = f"Error generating test case: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'content': None,
                'filename': None
            }
    
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
    
    def save_test_case_to_project(
        self,
        project_name: str,
        test_result: Dict[str, Any],
        project_manager = None
    ) -> Dict[str, Any]:
        """
        Save generated test case to a specific Playwright project.
        
        Args:
            project_name: Name of the Playwright project
            test_result: Result from generate_test_case()
            project_manager: Optional PlaywrightProjectManager instance
            
        Returns:
            Dictionary with save results
        """
        try:
            if not test_result.get('success'):
                return {
                    'success': False,
                    'error': 'Invalid test result provided'
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
            
            # Create tests directory if it doesn't exist
            tests_dir = project_path / 'tests'
            tests_dir.mkdir(exist_ok=True)
            
            # Write test file
            test_file_path = tests_dir / test_result['filename']
            
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_result['content'])
            
            logger.info(f"Saved test case to: {test_file_path}")
            
            return {
                'success': True,
                'file_path': str(test_file_path),
                'project_name': project_name,
                'test_case_name': test_result['test_case_name']
            }
            
        except Exception as e:
            error_msg = f"Error saving test case to project: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def list_project_test_cases(self, project_name: str, project_manager = None) -> List[Dict[str, Any]]:
        """
        List all test cases in a Playwright project.
        
        Args:
            project_name: Name of the Playwright project
            project_manager: Optional PlaywrightProjectManager instance
            
        Returns:
            List of test case information dictionaries
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
            
            tests_dir = project_path / 'tests'
            if not tests_dir.exists():
                return []
            
            test_cases = []
            
            # Find all .spec.ts files
            for test_file in tests_dir.glob('*.spec.ts'):
                try:
                    # Read file to extract basic info
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract test name from test() call
                    test_match = re.search(r"test\s*\(\s*['\"]([^'\"]+)['\"]", content)
                    test_name = test_match.group(1) if test_match else test_file.stem
                    
                    # Extract tags if present
                    tags_match = re.search(r"tag:\s*\[(.*?)\]", content, re.DOTALL)
                    tags = []
                    if tags_match:
                        tags_str = tags_match.group(1)
                        tags = [tag.strip().strip("'\"@") for tag in tags_str.split(',') if tag.strip()]
                    
                    test_cases.append({
                        'filename': test_file.name,
                        'test_name': test_name,
                        'tags': tags,
                        'file_path': str(test_file),
                        'size': test_file.stat().st_size
                    })
                    
                except Exception as e:
                    logger.warning(f"Error reading test file {test_file}: {str(e)}")
                    continue
            
            return sorted(test_cases, key=lambda x: x['filename'])
            
        except Exception as e:
            logger.error(f"Error listing project test cases: {str(e)}")
            return []


# Global instance for easy access
test_case_generator = PlaywrightTestCaseGenerator()


# Convenience functions
def generate_test_script(
    db: Session,
    test_case_id: str,
    project_name: str = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a test script.
    
    Args:
        db: Database session
        test_case_id: Test case ID
        project_name: Optional project name
        
    Returns:
        Dictionary with generation results
    """
    return test_case_generator.generate_test_case(db, test_case_id, project_name)


def save_test_script(
    project_name: str,
    test_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to save test script to project.
    
    Args:
        project_name: Name of the Playwright project
        test_result: Result from generate_test_script()
        
    Returns:
        Dictionary with save results
    """
    return test_case_generator.save_test_case_to_project(project_name, test_result)


def list_test_scripts(project_name: str) -> List[Dict[str, Any]]:
    """
    Convenience function to list project test scripts.
    
    Args:
        project_name: Name of the Playwright project
        
    Returns:
        List of test script information dictionaries
    """
    return test_case_generator.list_project_test_cases(project_name)
