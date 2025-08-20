from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.page import Page as PageModel
from ..models.page_element import PageLocator as PageLocatorModel
from ..models.user import User
from ..models.project import Project as ProjectModel
from ..schemas.page import PageCreate, PageUpdate, PageLocatorCreate, PageLocatorUpdate
from ..services.page_generator import generate_page_object_for_project


def create_page(db: Session, page: PageCreate, created_by: Optional[str] = None) -> PageModel:
    page_data = page.model_dump()
    if created_by:
        page_data['created_by'] = created_by
    db_page = PageModel(**page_data)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    
    # Generate page object file
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == page.project_id).first()
        if project and project.playwright_project_path:
            # Resolve folder name to absolute path using project manager
            from ..services.playwright_project import playwright_manager
            abs_path = str(playwright_manager.get_project_path(project.playwright_project_path))
            generate_page_object_for_project(db, str(page.project_id), abs_path)
    except Exception as e:
        print(f"Failed to generate page object: {e}")
    
    return db_page


def get_page(db: Session, page_id: str) -> Optional[PageModel]:
    page = db.query(PageModel).filter(PageModel.id == page_id).first()
    if page and page.created_by:
        author = db.query(User.username).filter(User.id == page.created_by).first()
        page.author_name = author[0] if author else None
    return page


def get_pages(db: Session, skip: int = 0, limit: int = 100) -> List[PageModel]:
    pages = db.query(PageModel).offset(skip).limit(limit).all()
    for p in pages:
        if p.created_by:
            author = db.query(User.username).filter(User.id == p.created_by).first()
            p.author_name = author[0] if author else None
    return pages


def get_pages_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 100) -> List[PageModel]:
    pages = (
        db.query(PageModel)
        .filter(PageModel.project_id == project_id)
        .order_by(PageModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    for p in pages:
        if p.created_by:
            author = db.query(User.username).filter(User.id == p.created_by).first()
            p.author_name = author[0] if author else None
    return pages


def update_page(db: Session, page_id: str, page: PageUpdate, updated_by: Optional[str] = None) -> Optional[PageModel]:
    db_page = get_page(db, page_id)
    if not db_page:
        return None
    update_data = page.model_dump(exclude_unset=True)
    if updated_by:
        update_data['updated_by'] = updated_by
    for field, value in update_data.items():
        setattr(db_page, field, value)
    db.commit()
    db.refresh(db_page)
    
    # Generate page object file
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == db_page.project_id).first()
        if project and project.playwright_project_path:
            from ..services.playwright_project import playwright_manager
            abs_path = str(playwright_manager.get_project_path(project.playwright_project_path))
            generate_page_object_for_project(db, str(db_page.project_id), abs_path)
    except Exception as e:
        print(f"Failed to generate page object: {e}")
    
    return db_page


def delete_page(db: Session, page_id: str) -> bool:
    db_page = get_page(db, page_id)
    if not db_page:
        return False
    
    project_id = str(db_page.project_id)
    project = db.query(ProjectModel).filter(ProjectModel.id == db_page.project_id).first()
    
    db.delete(db_page)
    db.commit()
    
    # Generate page object file
    try:
        if project and project.playwright_project_path:
            from ..services.playwright_project import playwright_manager
            abs_path = str(playwright_manager.get_project_path(project.playwright_project_path))
            generate_page_object_for_project(db, project_id, abs_path)
    except Exception as e:
        print(f"Failed to generate page object: {e}")
    
    return True


# Page locators CRUD
def create_page_locator(db: Session, locator: PageLocatorCreate, created_by: Optional[str] = None) -> PageLocatorModel:
    locator_data = locator.model_dump()
    if created_by:
        locator_data['created_by'] = created_by
    db_locator = PageLocatorModel(**locator_data)
    db.add(db_locator)
    db.commit()
    db.refresh(db_locator)
    
    # Generate page object file
    try:
        # Get the page first to get project_id
        page = db.query(PageModel).filter(PageModel.id == locator.page_id).first()
        if page:
            project = db.query(ProjectModel).filter(ProjectModel.id == page.project_id).first()
            if project and project.playwright_project_path:
                from ..services.playwright_project import playwright_manager
                abs_path = str(playwright_manager.get_project_path(project.playwright_project_path))
                generate_page_object_for_project(db, str(page.project_id), abs_path)
    except Exception as e:
        print(f"Failed to generate page object: {e}")
    
    if db_locator.created_by:
        author = db.query(User.username).filter(User.id == db_locator.created_by).first()
        db_locator.author_name = author[0] if author else None
    return db_locator


def get_page_locator(db: Session, locator_id: str) -> Optional[PageLocatorModel]:
    return db.query(PageLocatorModel).filter(PageLocatorModel.id == locator_id).first()


def get_page_locators_by_page(db: Session, page_id: str, skip: int = 0, limit: int = 100) -> list[PageLocatorModel]:
    locators = (
        db.query(PageLocatorModel)
        .filter(PageLocatorModel.page_id == page_id)
        .order_by(PageLocatorModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    for l in locators:
        if l.created_by:
            author = db.query(User.username).filter(User.id == l.created_by).first()
            l.author_name = author[0] if author else None
    return locators


def update_page_locator(db: Session, locator_id: str, locator: PageLocatorUpdate, updated_by: Optional[str] = None) -> Optional[PageLocatorModel]:
    db_locator = get_page_locator(db, locator_id)
    if not db_locator:
        return None
    update_data = locator.model_dump(exclude_unset=True)
    if updated_by:
        update_data['updated_by'] = updated_by
    for field, value in update_data.items():
        setattr(db_locator, field, value)
    db.commit()
    db.refresh(db_locator)
    
    # Generate page object file
    try:
        # Get the page first to get project_id
        page = db.query(PageModel).filter(PageModel.id == db_locator.page_id).first()
        if page:
            project = db.query(ProjectModel).filter(ProjectModel.id == page.project_id).first()
            if project and project.playwright_project_path:
                from ..services.playwright_project import playwright_manager
                abs_path = str(playwright_manager.get_project_path(project.playwright_project_path))
                generate_page_object_for_project(db, str(page.project_id), abs_path)
    except Exception as e:
        print(f"Failed to generate page object: {e}")
    
    if db_locator.created_by:
        author = db.query(User.username).filter(User.id == db_locator.created_by).first()
        db_locator.author_name = author[0] if author else None
    return db_locator


def delete_page_locator(db: Session, locator_id: str) -> bool:
    db_locator = get_page_locator(db, locator_id)
    if not db_locator:
        return False
    
    # Get the page first to get project_id
    page = db.query(PageModel).filter(PageModel.id == db_locator.page_id).first()
    project_id = str(page.project_id) if page else None
    
    db.delete(db_locator)
    db.commit()
    
    # Generate page object file
    try:
        if page and project_id:
            project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
            if project and project.playwright_project_path:
                generate_page_object_for_project(db, project_id, project.playwright_project_path)
    except Exception as e:
        print(f"Failed to generate page object: {e}")
    
    return True


