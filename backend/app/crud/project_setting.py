from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from ..models.project_setting import ProjectSetting
from ..schemas.project_setting import ProjectSettingCreate, ProjectSettingUpdate
import logging

logger = logging.getLogger(__name__)


def get_project_setting(db: Session, setting_id: str) -> Optional[ProjectSetting]:
    return db.query(ProjectSetting).filter(ProjectSetting.id == setting_id).first()


def get_project_settings(db: Session, skip: int = 0, limit: int = 100) -> List[ProjectSetting]:
    return db.query(ProjectSetting).offset(skip).limit(limit).all()


def get_settings_by_project(db: Session, project_id: str) -> List[ProjectSetting]:
    return db.query(ProjectSetting).filter(
        ProjectSetting.project_id == project_id
    ).order_by(ProjectSetting.key).all()


def get_setting_by_key(db: Session, project_id: str, key: str) -> Optional[ProjectSetting]:
    return db.query(ProjectSetting).filter(
        ProjectSetting.project_id == project_id,
        ProjectSetting.key == key
    ).first()


def create_project_setting(db: Session, setting: ProjectSettingCreate) -> ProjectSetting:
    # Convert timeout values from seconds to milliseconds before saving
    processed_value = setting.value
    if setting.key in ['TIMEOUT', 'EXPECT_TIMEOUT']:
        try:
            # Convert seconds to milliseconds
            seconds = float(setting.value)
            milliseconds = int(seconds * 1000)
            processed_value = str(milliseconds)
        except (ValueError, TypeError):
            # If conversion fails, keep original value
            processed_value = setting.value
    
    db_setting = ProjectSetting(
        project_id=setting.project_id,
        key=setting.key,
        value=processed_value,
        created_by=setting.created_by
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


async def update_project_setting(db: Session, setting_id: str, setting: ProjectSettingUpdate) -> Optional[ProjectSetting]:
    db_setting = get_project_setting(db, setting_id)
    if db_setting:
        update_data = setting.dict(exclude_unset=True)
        
        # Convert timeout values from seconds to milliseconds before saving
        if 'value' in update_data and db_setting.key in ['TIMEOUT', 'EXPECT_TIMEOUT']:
            try:
                # Convert seconds to milliseconds
                seconds = float(update_data['value'])
                milliseconds = int(seconds * 1000)
                update_data['value'] = str(milliseconds)
            except (ValueError, TypeError):
                # If conversion fails, keep original value
                pass
        
        for field, value in update_data.items():
            setattr(db_setting, field, value)
        
        db.commit()
        db.refresh(db_setting)
        
        # Regenerate playwright config if this is a Playwright setting
        if db_setting.key in ['BASE_URL', 'TIMEOUT', 'EXPECT_TIMEOUT', 'RETRIES', 'WORKERS', 
                             'VIEWPORT_WIDTH', 'VIEWPORT_HEIGHT', 'FULLY_PARALLEL', 'HEADLESS_MODE', 
                             'SCREENSHOT', 'VIDEO']:
            await _regenerate_playwright_config(db, str(db_setting.project_id))
    
    return db_setting


async def upsert_setting(db: Session, project_id: str, key: str, value: str, updated_by: str = None) -> ProjectSetting:
    """Create or update a setting"""
    # Convert timeout values from seconds to milliseconds before saving
    processed_value = value
    if key in ['TIMEOUT', 'EXPECT_TIMEOUT']:
        try:
            # Convert seconds to milliseconds
            seconds = float(value)
            milliseconds = int(seconds * 1000)
            processed_value = str(milliseconds)
        except (ValueError, TypeError):
            # If conversion fails, keep original value
            processed_value = value
    
    existing = get_setting_by_key(db, project_id, key)
    
    if existing:
        existing.value = processed_value
        existing.updated_by = updated_by
        db.commit()
        db.refresh(existing)
        
        # Regenerate playwright config if this is a Playwright setting
        if key in ['BASE_URL', 'TIMEOUT', 'EXPECT_TIMEOUT', 'RETRIES', 'WORKERS', 
                   'VIEWPORT_WIDTH', 'VIEWPORT_HEIGHT', 'FULLY_PARALLEL', 'HEADLESS_MODE', 
                   'SCREENSHOT', 'VIDEO']:
            await _regenerate_playwright_config(db, project_id)
        
        return existing
    else:
        new_setting = ProjectSetting(
            project_id=project_id,
            key=key,
            value=processed_value,
            created_by=updated_by
        )
        db.add(new_setting)
        db.commit()
        db.refresh(new_setting)
        
        # Regenerate playwright config if this is a Playwright setting
        if key in ['BASE_URL', 'TIMEOUT', 'EXPECT_TIMEOUT', 'RETRIES', 'WORKERS', 
                   'VIEWPORT_WIDTH', 'VIEWPORT_HEIGHT', 'FULLY_PARALLEL', 'HEADLESS_MODE', 
                   'SCREENSHOT', 'VIDEO']:
            await _regenerate_playwright_config(db, project_id)
        
        return new_setting


def delete_project_setting(db: Session, setting_id: str) -> bool:
    db_setting = get_project_setting(db, setting_id)
    if db_setting:
        db.delete(db_setting)
        db.commit()
        return True
    return False


def get_settings_as_dict(db: Session, project_id: str) -> Dict[str, str]:
    """Get all project settings as key-value dictionary"""
    settings = get_settings_by_project(db, project_id)
    return {setting.key: setting.value for setting in settings}


async def _regenerate_playwright_config(db: Session, project_id: str):
    """Regenerate playwright.config.ts when project settings are updated"""
    try:
        from ..models.project import Project
        from pathlib import Path
        
        # Get project name
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project not found for config regeneration: {project_id}")
            return
        
        # Get project settings
        settings = get_settings_by_project(db, project_id)
        settings_dict = {setting.key: setting.value for setting in settings}
        
        # Read the template file
        template_path = Path(__file__).parent.parent.parent / "template" / "playwright.config.ts.template"
        if not template_path.exists():
            logger.error(f"Template file not found: {template_path}")
            return
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace template variables with project settings
        config_content = template_content
        for key, value in settings_dict.items():
            placeholder = f"{{{{{key}}}}}"
            config_content = config_content.replace(placeholder, str(value))
        
        # Determine correct Playwright project directory using cleaned folder name
        try:
            from ..services.playwright_project import clean_name as clean_project_folder_name
            cleaned_name = clean_project_folder_name(project.name)
        except Exception:
            # Fallback: basic cleaning
            import re
            cleaned_name = re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', project.name.lower())).strip('-')

        # Write the generated config to the project directory
        project_dir = Path(__file__).parent.parent.parent.parent / "playwright_projects" / cleaned_name
        config_file_path = project_dir / "playwright.config.ts"
        
        if config_file_path.exists():
            # Backup existing file
            backup_path = config_file_path.with_suffix('.ts.backup')
            config_file_path.rename(backup_path)
            logger.info(f"Backed up existing config to {backup_path}")
        
        # Ensure directory exists and write new config file
        project_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info(f"Successfully regenerated playwright.config.ts for project '{project.name}'")
        
    except Exception as e:
        logger.error(f"Failed to regenerate playwright config for project {project_id}: {str(e)}") 