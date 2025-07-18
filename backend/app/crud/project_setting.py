from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from ..models.project_setting import ProjectSetting
from ..schemas.project_setting import ProjectSettingCreate, ProjectSettingUpdate


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
    db_setting = ProjectSetting(
        project_id=setting.project_id,
        key=setting.key,
        value=setting.value,
        created_by=setting.created_by
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


def update_project_setting(db: Session, setting_id: str, setting: ProjectSettingUpdate) -> Optional[ProjectSetting]:
    db_setting = get_project_setting(db, setting_id)
    if db_setting:
        update_data = setting.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_setting, field, value)
        
        db.commit()
        db.refresh(db_setting)
    return db_setting


def upsert_setting(db: Session, project_id: str, key: str, value: str, updated_by: str = None) -> ProjectSetting:
    """Create or update a setting"""
    existing = get_setting_by_key(db, project_id, key)
    
    if existing:
        existing.value = value
        existing.updated_by = updated_by
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_setting = ProjectSetting(
            project_id=project_id,
            key=key,
            value=value,
            created_by=updated_by
        )
        db.add(new_setting)
        db.commit()
        db.refresh(new_setting)
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