"""
Playwright Project Management Library

This module provides functionality to create and manage Playwright projects
with proper folder name cleanup.

Environment Variables:
    PLAYWRIGHT_PROJECTS_PATH: Custom path for storing Playwright projects.
                              Supports absolute paths and ~ (home directory expansion).
                              If not set, defaults to "playwright_projects/" in project root.

Examples:
    # Use default location (project_root/playwright_projects/)
    export PLAYWRIGHT_PROJECTS_PATH=""
    
    # Use custom absolute path
    export PLAYWRIGHT_PROJECTS_PATH="/custom/path/to/projects"
    
    # Use path relative to home directory
    export PLAYWRIGHT_PROJECTS_PATH="~/my-playwright-projects"
    
    # Use custom relative path (relative to project root)
    export PLAYWRIGHT_PROJECTS_PATH="custom_playwright_dir"
"""

import os
import re
import subprocess
import asyncio
import shutil
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FixtureIndexGenerator:
    """Generator for fixtures/index.ts file"""
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the fixture index generator.
        
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
    
    def _load_template(self) -> str:
        """Load the index fixture template"""
        template_path = self.template_dir / "index.fixture.template"
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _render_template(self, template: str, fixtures: List[Dict[str, Any]]) -> str:
        """
        Render template with fixtures data using simple regex-based templating.
        
        Args:
            template: Template content
            fixtures: List of fixture dictionaries with importName, exportName, fileName
            
        Returns:
            Rendered content
        """
        rendered = template
        
        # Handle {{#if fixtures.length}} block
        if fixtures:
            # Remove the {{#if fixtures.length}} and {{else}} blocks, keep the content
            rendered = re.sub(r'{{\s*#if\s+fixtures\.length\s*}}(.*?){{\s*else\s*}}.*?{{\s*/if\s*}}', r'\1', rendered, flags=re.DOTALL)
        else:
            # Remove the {{#if fixtures.length}} block, keep the {{else}} content
            rendered = re.sub(r'{{\s*#if\s+fixtures\.length\s*}}.*?{{\s*else\s*}}(.*?){{\s*/if\s*}}', r'\1', rendered, flags=re.DOTALL)
        
        if fixtures:
            # Process {{#each fixtures}} loops
            each_pattern = r'{{\s*#each\s+fixtures\s*}}(.*?){{\s*/each\s*}}'
            each_matches = re.findall(each_pattern, rendered, flags=re.DOTALL)
            
            for each_content in each_matches:
                loop_result = ""
                for i, fixture in enumerate(fixtures):
                    loop_item = each_content
                    
                    # Replace {{this.importName}}, {{this.exportName}}, {{this.fileName}}
                    loop_item = loop_item.replace('{{this.importName}}', fixture.get('importName', ''))
                    loop_item = loop_item.replace('{{this.exportName}}', fixture.get('exportName', ''))
                    loop_item = loop_item.replace('{{this.fileName}}', fixture.get('fileName', ''))
                    
                    # Handle {{#unless @last}}
                    if i < len(fixtures) - 1:
                        loop_item = re.sub(r'{{\s*#unless\s+@last\s*}}(.*?){{\s*/unless\s*}}', r'\1', loop_item, flags=re.DOTALL)
                    else:
                        loop_item = re.sub(r'{{\s*#unless\s+@last\s*}}.*?{{\s*/unless\s*}}', '', loop_item, flags=re.DOTALL)
                    
                    loop_result += loop_item
                
                # Replace the entire {{#each}} block with the result
                rendered = re.sub(each_pattern, loop_result, rendered, flags=re.DOTALL, count=1)
        else:
            # Remove {{#each fixtures}} blocks
            rendered = re.sub(r'{{\s*#each\s+fixtures\s*}}.*?{{\s*/each\s*}}', '', rendered, flags=re.DOTALL)
        
        # Clean up any remaining template syntax
        rendered = re.sub(r'{{\s*[^}]+\s*}}', '', rendered)
        rendered = re.sub(r'\n\s*\n\s*\n', '\n\n', rendered)  # Remove excessive blank lines
        
        return rendered
    
    def generate_index(self, fixtures: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate fixtures/index.ts content.
        
        Args:
            fixtures: List of fixture data dictionaries
            
        Returns:
            Dictionary with generation results
        """
        try:
            if fixtures is None:
                fixtures = []
            
            # Load template
            template = self._load_template()
            
            # Render template
            rendered_content = self._render_template(template, fixtures)
            
            # Apply TypeScript formatting if available
            try:
                from ..utils.typescript_formatter import format_typescript_code
                formatted_content = format_typescript_code(rendered_content)
                rendered_content = formatted_content
                logger.debug("Applied TypeScript formatting to generated index.ts")
            except ImportError:
                logger.debug("TypeScript formatter not available, using unformatted content")
            except Exception as e:
                logger.warning(f"Failed to format generated index.ts: {str(e)}")
            
            return {
                'success': True,
                'content': rendered_content,
                'filename': 'index.ts'
            }
            
        except Exception as e:
            error_msg = f"Error generating fixtures index: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'content': None,
                'filename': None
            }


class PlaywrightProjectManager:
    """Manager class for creating and managing Playwright projects."""
    
    def __init__(self, base_projects_dir: str = None):
        """
        Initialize the Playwright project manager.
        
        Args:
            base_projects_dir: Base directory for Playwright projects.
                              If None, will use environment variable PLAYWRIGHT_PROJECTS_PATH
                              or default to "playwright_projects"
        """
        # Determine the base directory path
        if base_projects_dir is None:
            # Check environment variable first
            env_path = os.getenv('PLAYWRIGHT_PROJECTS_PATH')
            if env_path:
                # Handle paths starting with ~ (home directory)
                if env_path.startswith('~'):
                    self.base_projects_dir = Path(env_path).expanduser().resolve()
                elif Path(env_path).is_absolute():
                    self.base_projects_dir = Path(env_path).resolve()
                else:
                    # Relative path - resolve from project root
                    current_file = Path(__file__)
                    project_root = current_file.parent.parent.parent.parent  # Go up 4 levels
                    self.base_projects_dir = project_root / env_path
            else:
                # Use default relative to project root
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent.parent  # Go up 4 levels
                self.base_projects_dir = project_root / "playwright_projects"
        else:
            # Use provided path (could be relative or absolute)
            if base_projects_dir.startswith('~'):
                self.base_projects_dir = Path(base_projects_dir).expanduser().resolve()
            elif Path(base_projects_dir).is_absolute():
                self.base_projects_dir = Path(base_projects_dir).resolve()
            else:
                # Relative path - resolve from project root
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent.parent
                self.base_projects_dir = project_root / base_projects_dir
        
        # Create directory if it doesn't exist
        self.base_projects_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Playwright projects directory: {self.base_projects_dir.absolute()}")
    
    def clean_folder_name(self, name: str) -> str:
        """
        Clean folder name to only contain a-z, 0-9, and hyphens.
        
        Args:
            name: Original folder name
            
        Returns:
            Cleaned folder name with only allowed characters
        """
        # Convert to lowercase
        cleaned = name.lower()
        
        # Replace spaces and underscores with hyphens
        cleaned = re.sub(r'[\s_]+', '-', cleaned)
        
        # Keep only a-z, 0-9, and hyphens
        cleaned = re.sub(r'[^a-z0-9\-]', '', cleaned)
        
        # Remove multiple consecutive hyphens
        cleaned = re.sub(r'-+', '-', cleaned)
        
        # Remove leading and trailing hyphens
        cleaned = cleaned.strip('-')
        
        # Ensure the name is not empty
        if not cleaned:
            cleaned = 'project'
            
        return cleaned
    
    def _setup_custom_project_structure(self, project_path: Path) -> bool:
        """
        Clean up default Playwright structure and create custom folders.
        
        Args:
            project_path: Path to the created Playwright project
            
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            # Remove default folders if they exist
            folders_to_remove = ['tests', 'tests-examples']
            for folder_name in folders_to_remove:
                folder_path = project_path / folder_name
                if folder_path.exists():
                    shutil.rmtree(folder_path)
                    logger.info(f"Removed default folder: {folder_path}")
            
            # Create custom folders
            folders_to_create = ['fixtures', 'tests']
            for folder_name in folders_to_create:
                folder_path = project_path / folder_name
                folder_path.mkdir(exist_ok=True)
                logger.info(f"Created custom folder: {folder_path}")
                
                # Create .gitkeep file to ensure folder is tracked in git
                gitkeep_file = folder_path / '.gitkeep'
                gitkeep_file.touch()
            
            # Create fixtures/index.ts with empty fixtures list
            fixtures_folder = project_path / 'fixtures'
            index_generator = FixtureIndexGenerator()
            
            # Generate index.ts with no fixtures (empty project)
            index_result = index_generator.generate_index([])
            
            if index_result.get('success'):
                index_path = fixtures_folder / 'index.ts'
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(index_result['content'])
                logger.info(f"Created fixtures/index.ts: {index_path}")
            else:
                logger.warning(f"Failed to generate fixtures/index.ts: {index_result.get('error')}")
                # Don't fail the entire setup if index.ts generation fails
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up custom project structure: {str(e)}")
            return False
    
    async def create_playwright_project(
        self, 
        project_name: str, 
        force_recreate: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new Playwright project with cleaned folder name.
        
        Args:
            project_name: Original project name
            force_recreate: Whether to recreate if project already exists
            
        Returns:
            Tuple of (success, cleaned_folder_name, error_message)
        """
        try:
            # Clean the folder name
            cleaned_name = self.clean_folder_name(project_name)
            project_path = self.base_projects_dir / cleaned_name
            
            # Check if project already exists
            if project_path.exists():
                if not force_recreate:
                    return False, cleaned_name, f"Project '{cleaned_name}' already exists"
                else:
                    # Remove existing project
                    shutil.rmtree(project_path)
                    logger.info(f"Removed existing project: {project_path}")
            
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created project directory: {project_path}")
            
            # Run npx create-playwright command
            cmd = [
                "npx", 
                "create-playwright@latest", 
                "--quiet", 
                "--install-deps"
            ]
            
            # Execute the command in the project directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully created Playwright project: {cleaned_name}")
                
                # Set up custom project structure (remove default folders, create custom ones)
                structure_success = self._setup_custom_project_structure(project_path)
                if structure_success:
                    logger.info(f"Successfully set up custom structure for project: {cleaned_name}")
                else:
                    logger.warning(f"Playwright project created but custom structure setup failed for: {cleaned_name}")
                
                return True, cleaned_name, None
            else:
                error_msg = f"Failed to create Playwright project. Error: {stderr.decode()}"
                logger.error(error_msg)
                
                # Clean up failed project directory
                if project_path.exists():
                    shutil.rmtree(project_path)
                
                return False, cleaned_name, error_msg
                
        except Exception as e:
            error_msg = f"Exception occurred while creating project: {str(e)}"
            logger.error(error_msg)
            return False, cleaned_name if 'cleaned_name' in locals() else project_name, error_msg
    
    def list_projects(self) -> list[str]:
        """
        List all existing Playwright projects.
        
        Returns:
            List of project folder names
        """
        try:
            if not self.base_projects_dir.exists():
                return []
            
            projects = []
            for item in self.base_projects_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    projects.append(item.name)
            
            return sorted(projects)
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return []
    
    def get_project_path(self, project_name: str) -> Optional[Path]:
        """
        Get the full path to a project directory.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to project directory or None if not found
        """
        cleaned_name = self.clean_folder_name(project_name)
        project_path = self.base_projects_dir / cleaned_name
        
        if project_path.exists() and project_path.is_dir():
            return project_path
        
        return None
    
    def delete_project(self, project_name: str) -> Tuple[bool, str]:
        """
        Delete a Playwright project.
        
        Args:
            project_name: Name of the project to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            cleaned_name = self.clean_folder_name(project_name)
            project_path = self.base_projects_dir / cleaned_name
            
            if not project_path.exists():
                return False, f"Project '{cleaned_name}' does not exist"
            
            shutil.rmtree(project_path)
            logger.info(f"Deleted project: {cleaned_name}")
            
            return True, f"Successfully deleted project '{cleaned_name}'"
            
        except Exception as e:
            error_msg = f"Error deleting project: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Global instances for easy access
playwright_manager = PlaywrightProjectManager()
fixture_index_generator = FixtureIndexGenerator()


# Convenience functions
async def create_project(project_name: str, force_recreate: bool = False) -> Tuple[bool, str, Optional[str]]:
    """
    Convenience function to create a Playwright project.
    
    Args:
        project_name: Original project name
        force_recreate: Whether to recreate if project already exists
        
    Returns:
        Tuple of (success, cleaned_folder_name, error_message)
    """
    return await playwright_manager.create_playwright_project(project_name, force_recreate)


def clean_name(name: str) -> str:
    """
    Convenience function to clean a folder name.
    
    Args:
        name: Original name
        
    Returns:
        Cleaned name
    """
    return playwright_manager.clean_folder_name(name)


def generate_fixtures_index(fixtures: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to generate fixtures/index.ts content.
    
    Args:
        fixtures: List of fixture data dictionaries
        
    Returns:
        Dictionary with generation results
    """
    return fixture_index_generator.generate_index(fixtures)


def save_fixtures_index(project_name: str, index_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save fixtures index to project.
    
    Args:
        project_name: Name of the Playwright project
        index_result: Result from generate_fixtures_index()
        
    Returns:
        Dictionary with save results
    """
    try:
        if not index_result.get('success'):
            return {
                'success': False,
                'error': 'Invalid index result provided'
            }
        
        # Get project path
        project_path = playwright_manager.base_projects_dir / clean_name(project_name)
        if not project_path.exists():
            return {
                'success': False,
                'error': f'Project not found: {project_name}'
            }
        
        # Save to fixtures/index.ts
        fixtures_folder = project_path / 'fixtures'
        fixtures_folder.mkdir(exist_ok=True)
        
        index_path = fixtures_folder / 'index.ts'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_result['content'])
        
        return {
            'success': True,
            'file_path': str(index_path),
            'project_name': project_name
        }
        
    except Exception as e:
        error_msg = f"Error saving fixtures index: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }


async def regenerate_fixtures_index_for_project(db_session, project_id: str) -> bool:
    """
    Regenerate fixtures/index.ts for a project based on all fixtures in database.
    
    Args:
        db_session: Database session
        project_id: Project ID
        
    Returns:
        bool: True if regeneration successful, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from ..models.project import Project
        from ..models.fixture import Fixture
        
        # Get project from database
        project = db_session.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project not found: {project_id}")
            return False
        
        # Get all fixtures for this project
        fixtures = db_session.query(Fixture).filter(Fixture.project_id == project_id).all()
        
        # Convert fixtures to template format
        fixtures_data = []
        for fixture in fixtures:
            # Clean fixture name to create export name (proper camelCase)
            # Remove special characters and split by spaces/dashes/underscores
            import re
            cleaned = re.sub(r'[^\w\s]', '', fixture.name)  # Remove special chars except spaces
            words = re.split(r'[\s\-_]+', cleaned.lower())  # Split by spaces, dashes, underscores
            words = [word for word in words if word]  # Remove empty strings
            
            if not words:
                export_name = 'fixture'
            else:
                # First word lowercase, rest title case (proper camelCase)
                export_name = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
            
            # Ensure it starts with a letter
            if not export_name[0].isalpha():
                export_name = 'fixture' + export_name.capitalize()
            
            fixtures_data.append({
                'importName': export_name,
                'exportName': export_name,
                'fileName': f'{export_name}.fixture'
            })
        
        # Generate index.ts content
        index_result = generate_fixtures_index(fixtures_data)
        
        if not index_result.get('success'):
            logger.error(f"Failed to generate fixtures index for project {project_id}: {index_result.get('error')}")
            return False
        
        # Save index.ts to project
        save_result = save_fixtures_index(project.name, index_result)
        
        if not save_result.get('success'):
            logger.error(f"Failed to save fixtures index for project {project_id}: {save_result.get('error')}")
            return False
        
        logger.info(f"Successfully regenerated fixtures/index.ts for project {project.name}: {save_result.get('file_path')}")
        return True
        
    except Exception as e:
        logger.error(f"Error regenerating fixtures index for project {project_id}: {str(e)}")
        return False


def list_all_projects() -> list[str]:
    """
    Convenience function to list all projects.
    
    Returns:
        List of project names
    """
    return playwright_manager.list_projects()


def get_project_directory(project_name: str) -> Optional[Path]:
    """
    Convenience function to get project directory path.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Path to project directory or None
    """
    return playwright_manager.get_project_path(project_name)


def get_config_info() -> dict:
    """
    Get current configuration information.
    
    Returns:
        Dictionary with configuration details
    """
    env_path = os.getenv('PLAYWRIGHT_PROJECTS_PATH')
    
    # Calculate what the path would be with current environment
    if env_path:
        # Handle paths starting with ~ (home directory)
        if env_path.startswith('~'):
            calculated_path = Path(env_path).expanduser().resolve()
        elif Path(env_path).is_absolute():
            calculated_path = Path(env_path).resolve()
        else:
            # Relative path - resolve from project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            calculated_path = project_root / env_path
    else:
        # Default path
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        calculated_path = project_root / "playwright_projects"
    
    return {
        "environment_variable": env_path,
        "using_env_var": bool(env_path),
        "current_manager_path": str(playwright_manager.base_projects_dir.absolute()),
        "calculated_path_from_env": str(calculated_path.absolute()),
        "path_exists": calculated_path.exists(),
        "default_path": "playwright_projects/ (relative to project root)",
        "note": "Restart required for environment variable changes to take effect in existing manager instance"
    }


def create_fresh_manager() -> PlaywrightProjectManager:
    """
    Create a new PlaywrightProjectManager instance with current environment variables.
    
    Returns:
        New PlaywrightProjectManager instance
    """
    return PlaywrightProjectManager()
