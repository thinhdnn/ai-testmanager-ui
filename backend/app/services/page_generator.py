import os
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.page import Page as PageModel
from ..models.page_element import PageLocator as PageLocatorModel
from ..models.project import Project as ProjectModel


class PageGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.pages_folder = os.path.join(project_path, "pages")
        self.template_path = os.path.join(os.path.dirname(__file__), "..", "..", "template", "page.template")
        
    def generate_page_object(self, db: Session, project_id: str) -> bool:
        """Generate page object file for a project"""
        try:
            # Get project
            project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
            if not project:
                return False
                
            # Get all pages with their locators
            pages = db.query(PageModel).filter(PageModel.project_id == project_id).all()
            
            if not pages:
                return False
                
            # Prepare flat content lines
            locator_lines: List[str] = []
            for page in pages:
                page_name_camel = self._to_camel_case(page.name)
                # Get locators for this page
                locators = db.query(PageLocatorModel).filter(PageLocatorModel.page_id == page.id).all()
                if not locators:
                    continue
                locator_lines.append(f"  // {page.name} Page")
                for loc in locators:
                    key_camel = self._to_camel_case(loc.locator_key)
                    value = loc.locator_value
                    locator_lines.append(f"  readonly {page_name_camel}_{key_camel} = '{value}';")
                locator_lines.append("")
            content_block = "\n".join(locator_lines).rstrip() + ("\n" if locator_lines else "")
            
            # Read template
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            generated_content = template_content.replace("{{content}}", content_block)
            
            # Ensure pages folder exists
            os.makedirs(self.pages_folder, exist_ok=True)
            
            # Write generated file
            output_file = os.path.join(self.pages_folder, "AllPage.ts")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(generated_content)
                
            return True
            
        except Exception as e:
            print(f"Error generating page object: {e}")
            return False
    
    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase"""
        if not text:
            return ""
        
        # Remove special characters and split by spaces
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        
        if not words:
            return ""
        
        # Convert to camelCase
        result = words[0].lower()
        for word in words[1:]:
            result += word.capitalize()
            
        return result


def generate_page_object_for_project(db: Session, project_id: str, project_path: str) -> bool:
    """Helper function to generate page object for a project"""
    generator = PageGenerator(project_path)
    return generator.generate_page_object(db, project_id)
