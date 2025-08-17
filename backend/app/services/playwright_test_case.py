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
        
        # Handle fixture-related logic FIRST - before simple variable substitution
        fixtures = context.get('fixtures', [])
        has_extend_fixtures = any(f.get('mode') == 'extend' for f in fixtures)
        
        logger.info(f"=== TEMPLATE RENDERING DEBUG ===")
        logger.info(f"Fixtures in context: {len(fixtures)}")
        for i, fixture in enumerate(fixtures):
            logger.info(f"  Fixture {i+1}: {fixture.get('name')} (mode: {fixture.get('mode')}, exportName: {fixture.get('exportName')})")
        
        logger.info(f"Has extend fixtures: {has_extend_fixtures}")
        
        # Build fixture parameters for function signature
        fixture_params = []
        if has_extend_fixtures:
            for fixture in fixtures:
                if fixture.get('mode') == 'extend':
                    fixture_params.append(fixture.get('exportName', 'fixture'))
        
        fixture_param_str = ', ' + ', '.join(fixture_params) if fixture_params else ''
        logger.info(f"Fixture params: {fixture_params}")
        logger.info(f"Fixture param string: '{fixture_param_str}'")
        
        # Handle the specific pattern: {{#each fixtures}}{{#if (eq mode "extend")}}, {{exportName}}{{/if}}{{/each}}
        if has_extend_fixtures:
            # The actual template pattern is: page{{#each fixtures}}{{#if (eq mode "extend")}}, {{exportName}}{{/if}}{{/each}}
            # We need to replace this entire pattern with: page, fixture1, fixture2, etc.
            
            logger.info(f"Looking for fixture pattern in template...")
            pattern_match = re.search(r'page{{#each fixtures}}{{#if \(eq mode "extend"\)}}, {{exportName}}{{/if}}{{/each}}', template, re.DOTALL)
            if pattern_match:
                logger.info(f"Found pattern in template: {repr(pattern_match.group(0))}")
            else:
                logger.warning(f"Pattern not found in template with current regex")
                # Try to find any pattern that contains the fixture logic
                any_fixture_pattern = re.search(r'{{#each fixtures}}.*?{{/each}}', template, re.DOTALL)
                if any_fixture_pattern:
                    logger.info(f"Found any fixture pattern: {repr(any_fixture_pattern.group(0))}")
            
            # Replace the pattern - use the exact pattern from the template
            exact_pattern = r'page{{#each fixtures}}{{#if \(eq mode "extend"\)}}, {{exportName}}{{/if}}{{/each}}'
            replacement = f'page{fixture_param_str}'
            logger.info(f"Replacing pattern: {exact_pattern}")
            logger.info(f"With replacement: {replacement}")
            
            # Check if pattern exists in rendered template before replacement
            pattern_in_rendered = re.search(exact_pattern, rendered, re.DOTALL)
            if pattern_in_rendered:
                logger.info(f"Pattern found in rendered template before replacement")
            else:
                logger.warning(f"Pattern NOT found in rendered template before replacement")
                logger.info(f"Rendered template content: {repr(rendered[:200])}...")
            
            rendered = re.sub(exact_pattern, replacement, rendered, flags=re.DOTALL)
            logger.info(f"After replacement, fixture_param_str in rendered: {fixture_param_str in rendered}")
            
            # Check if replacement worked
            if fixture_param_str in rendered:
                logger.info(f"✅ Fixture parameter successfully added to template")
            else:
                logger.warning(f"❌ Fixture parameter was NOT added to template")
        else:
            # Remove the entire pattern if no extend fixtures
            exact_pattern = r'page{{#each fixtures}}{{#if \(eq mode "extend"\)}}, {{exportName}}{{/if}}{{/each}}'
            rendered = re.sub(exact_pattern, 'page', rendered, flags=re.DOTALL)
            logger.info(f"No extend fixtures, removed pattern")
        
        logger.info(f"=== END TEMPLATE RENDERING DEBUG ===")
        
        # Handle simple variable substitution AFTER fixtures
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
            logger.info(f"=== FIXTURE COLLECTION DEBUG ===")
            logger.info(f"Direct fixtures from test_case_fixtures table: {len(fixtures_data)}")
            for i, fixture in enumerate(fixtures_data):
                logger.info(f"  Direct fixture {i+1}: {fixture.get('name')} (type: {fixture.get('type')})")
            
            # Also collect fixtures that are referenced by steps
            referenced_fixtures = set()
            for step in steps:
                if step.referenced_fixture_id:
                    referenced_fixtures.add(step.referenced_fixture_id)
                    logger.info(f"  Step '{step.action}' references fixture: {step.referenced_fixture_id}")
                else:
                    logger.info(f"  Step '{step.action}' has no referenced fixture")
            
            logger.info(f"Total referenced fixtures found: {len(referenced_fixtures)}")
            
            # Get referenced fixtures data - use referenced_fixture_type from steps
            if referenced_fixtures:
                for step in steps:
                    if step.referenced_fixture_id and step.referenced_fixture_type:
                        fixture_id = step.referenced_fixture_id
                        fixture_type = step.referenced_fixture_type
                        fixture_name = step.referenced_fixture_name or "Unknown Fixture"
                        
                        logger.info(f"  Step '{step.action}' has fixture: {fixture_name} (type: {fixture_type})")
                        
                        # Check if this fixture is already in fixtures_data
                        if not any(f['fixture_id'] == str(fixture_id) for f in fixtures_data):
                            logger.info(f"    Adding fixture to fixtures_data")
                            fixtures_data.append({
                                'fixture_id': str(fixture_id),
                                'name': fixture_name,
                                'type': fixture_type,
                                'playwright_script': None,  # We don't have this from step
                                'order': len(fixtures_data) + 1,  # Add to end
                                'created_at': step.created_at,
                                'created_by': step.created_by
                            })
                        else:
                            logger.info(f"    Fixture already in fixtures_data")
            else:
                logger.info("  No referenced fixtures found in steps")
            
            logger.info(f"Final fixtures_data count: {len(fixtures_data)}")
            for i, fixture in enumerate(fixtures_data):
                logger.info(f"  Final fixture {i+1}: {fixture.get('name')} (type: {fixture.get('type')})")
            logger.info(f"=== END FIXTURE COLLECTION DEBUG ===")
            
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
                    'data': step.data,
                    'referenced_fixture_id': step.referenced_fixture_id,
                    'referenced_fixture_type': step.referenced_fixture_type,
                    'referenced_fixture_name': step.referenced_fixture_name
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
                'template_context': context,
                'test_case_db': test_case  # Add test case database object for file path lookup
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
        project_manager = None,
        test_case_db = None
    ) -> Dict[str, Any]:
        """
        Save generated test case to a specific Playwright project.
        If test_case_db is provided and has test_file_path, rename existing file.
        Otherwise, create new file.
        
        Args:
            project_name: Name of the Playwright project
            test_result: Result from generate_test_case()
            project_manager: Optional PlaywrightProjectManager instance
            test_case_db: Optional TestCase database object for file path lookup
            
        Returns:
            Dictionary with save results
        """
        try:
            logger.info(f"=== SAVE TEST CASE DEBUG START ===")
            logger.info(f"Project name: {project_name}")
            logger.info(f"Test result success: {test_result.get('success')}")
            logger.info(f"Test case DB provided: {test_case_db is not None}")
            
            if not test_result.get('success'):
                logger.error("Invalid test result provided")
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
            logger.info(f"Project path: {project_path}")
            
            if not project_path:
                logger.error(f"Project '{project_name}' not found")
                return {
                    'success': False,
                    'error': f"Project '{project_name}' not found"
                }
            
            # Create tests directory if it doesn't exist
            tests_dir = project_path / 'tests'
            tests_dir.mkdir(exist_ok=True)
            logger.info(f"Tests directory: {tests_dir}")
            logger.info(f"Tests directory exists: {tests_dir.exists()}")
            
            # Determine target file path
            target_file_path = tests_dir / test_result['filename']
            logger.info(f"Target file path: {target_file_path}")
            logger.info(f"Target file exists: {target_file_path.exists()}")
            
            # If test_case_db exists and has test_file_path, try to rename existing file
            if test_case_db and test_case_db.test_file_path:
                logger.info(f"Test case DB has test_file_path: {test_case_db.test_file_path}")
                try:
                    # Check if old file exists
                    old_file_path = Path(test_case_db.test_file_path)
                    logger.info(f"Old file path: {old_file_path}")
                    logger.info(f"Old file exists: {old_file_path.exists()}")
                    logger.info(f"Old file equals target: {old_file_path == target_file_path}")
                    
                    if old_file_path.exists() and old_file_path != target_file_path:
                        # Rename old file to new name
                        logger.info(f"Renaming old file: {old_file_path} -> {target_file_path}")
                        old_file_path.rename(target_file_path)
                        logger.info(f"Successfully renamed file")
                    elif old_file_path.exists() and old_file_path == target_file_path:
                        # Same path, just overwrite content
                        logger.info(f"Same path detected, overwriting content: {target_file_path}")
                        with open(target_file_path, 'w', encoding='utf-8') as f:
                            f.write(test_result['content'])
                        logger.info(f"Successfully overwrote file content")
                    else:
                        # Old file doesn't exist, create new one
                        logger.info(f"Old file doesn't exist, creating new file: {target_file_path}")
                        with open(target_file_path, 'w', encoding='utf-8') as f:
                            f.write(test_result['content'])
                        logger.info(f"Successfully created new file")
                except Exception as e:
                    logger.warning(f"Failed to rename existing file, creating new one: {str(e)}")
                    # Fallback to creating new file
                    logger.info(f"Fallback: Creating new file with content")
                    with open(target_file_path, 'w', encoding='utf-8') as f:
                        f.write(test_result['content'])
                    logger.info(f"Fallback: Successfully created file")
            else:
                # No existing file path, create new file
                logger.info(f"No existing file path, creating new file: {target_file_path}")
                with open(target_file_path, 'w', encoding='utf-8') as f:
                    f.write(test_result['content'])
                logger.info(f"Successfully created new file")
            
            # Verify file was written
            if target_file_path.exists():
                logger.info(f"File exists after save: {target_file_path}")
                logger.info(f"File size: {target_file_path.stat().st_size} bytes")
                # Read first few lines to verify content
                try:
                    with open(target_file_path, 'r', encoding='utf-8') as f:
                        first_lines = []
                        for _ in range(5):
                            line = f.readline().strip()
                            if line:
                                first_lines.append(line)
                    logger.info(f"First few lines: {first_lines}")
                except Exception as e:
                    logger.warning(f"Could not read file content: {str(e)}")
            else:
                logger.error(f"File does not exist after save: {target_file_path}")
            
            # Update test case database with new file path
            if test_case_db:
                try:
                    from sqlalchemy.orm import Session
                    if hasattr(test_case_db, '__table__'):  # Check if it's a SQLAlchemy model
                        # Store relative path from project directory instead of absolute path
                        relative_path = f"tests/{test_result['filename']}"
                        test_case_db.test_file_path = relative_path
                        # Note: This requires the db session to be committed by the caller
                        logger.info(f"Updated test case {test_case_db.id} with new file path: {relative_path}")
                    else:
                        logger.warning(f"Test case DB is not a SQLAlchemy model")
                except Exception as e:
                    logger.warning(f"Failed to update test case file path in database: {str(e)}")
            
            logger.info(f"=== SAVE TEST CASE DEBUG END ===")
            logger.info(f"Saved test case to: {target_file_path}")
            
            return {
                'success': True,
                'file_path': f"tests/{test_result['filename']}",  # Relative path from project directory
                'project_name': project_name,
                'test_case_name': test_result['test_case_name'],
                'renamed': test_case_db and test_case_db.test_file_path is not None
            }
            
        except Exception as e:
            error_msg = f"Error saving test case to project: {str(e)}"
            logger.error(f"=== SAVE TEST CASE ERROR ===")
            logger.error(error_msg)
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
                        'file_path': f"tests/{test_file.name}",  # Relative path from project directory
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
    # Extract test_case_db from test_result if available
    test_case_db = test_result.get('test_case_db')
    return test_case_generator.save_test_case_to_project(project_name, test_result, test_case_db=test_case_db)


def list_test_scripts(project_name: str) -> List[Dict[str, Any]]:
    """
    Convenience function to list project test scripts.
    
    Args:
        project_name: Name of the Playwright project
        
    Returns:
        List of test script information dictionaries
    """
    return test_case_generator.list_project_test_cases(project_name)
