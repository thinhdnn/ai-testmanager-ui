from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...schemas.page import Page, PageCreate, PageUpdate, PageLocator, PageLocatorCreate, PageLocatorUpdate
from ...crud import page as crud_page
from ...auth import current_active_user
from ...models.user import User
from ...crud import project as crud_project
from ...services.page_generator import generate_page_object_for_project
from ...models.project import Project as ProjectModel


router = APIRouter()


@router.post("/", response_model=Page, status_code=status.HTTP_201_CREATED)
def create_page(
    page: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    # Ensure project exists
    project = crud_project.get_project(db, project_id=str(page.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud_page.create_page(db=db, page=page, created_by=str(current_user.id))


@router.get("/", response_model=List[Page])
def read_pages(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    if project_id:
        # Ensure project exists
        project = crud_project.get_project(db, project_id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return crud_page.get_pages_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return crud_page.get_pages(db, skip=skip, limit=limit)


@router.get("/{page_id}", response_model=Page)
def read_page(
    page_id: str,
    db: Session = Depends(get_db)
):
    db_page = crud_page.get_page(db, page_id=page_id)
    if not db_page:
        raise HTTPException(status_code=404, detail="Page not found")
    return db_page


@router.put("/{page_id}", response_model=Page)
def update_page(
    page_id: str,
    page: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    db_page = crud_page.get_page(db, page_id=page_id)
    if not db_page:
        raise HTTPException(status_code=404, detail="Page not found")
    updated = crud_page.update_page(db, page_id=page_id, page=page, updated_by=str(current_user.id))
    return updated


@router.delete("/{page_id}")
def delete_page(
    page_id: str,
    db: Session = Depends(get_db)
):
    db_page = crud_page.get_page(db, page_id=page_id)
    if not db_page:
        raise HTTPException(status_code=404, detail="Page not found")
    crud_page.delete_page(db, page_id=page_id)
    return {"message": "Page deleted successfully"}


@router.post("/{project_id}/regenerate-page-object")
def regenerate_page_object(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    """Manually regenerate page object file for a project"""
    # Check if project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.playwright_project_path:
        raise HTTPException(status_code=400, detail="Project has no Playwright path configured")
    
    try:
        # Resolve folder name to absolute path using project manager
        from ...services.playwright_project import playwright_manager
        abs_path = str(playwright_manager.get_project_path(project.playwright_project_path))
        success = generate_page_object_for_project(db, project_id, abs_path)
        if success:
            return {"message": "Page object file generated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate page object file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating page object: {str(e)}")


# ============ PAGE LOCATORS NESTED ROUTES ============

@router.get("/{page_id}/locators", response_model=List[PageLocator])
def list_page_locators(
    page_id: str,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    page = crud_page.get_page(db, page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return crud_page.get_page_locators_by_page(db, page_id=page_id, skip=skip, limit=limit)


@router.post("/{page_id}/locators", response_model=PageLocator, status_code=status.HTTP_201_CREATED)
def create_page_locator(
    page_id: str,
    locator: PageLocatorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    page = crud_page.get_page(db, page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    # Enforce URL page_id precedence
    locator_data = locator.model_dump()
    locator_data['page_id'] = page_id
    locator_with_page = PageLocatorCreate(**locator_data)
    return crud_page.create_page_locator(db, locator_with_page, created_by=str(current_user.id))


@router.put("/{page_id}/locators/{locator_id}", response_model=PageLocator)
def update_page_locator(
    page_id: str,
    locator_id: str,
    locator: PageLocatorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    page = crud_page.get_page(db, page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    updated = crud_page.update_page_locator(db, locator_id, locator, updated_by=str(current_user.id))
    if not updated:
        raise HTTPException(status_code=404, detail="Locator not found")
    return updated


@router.delete("/{page_id}/locators/{locator_id}")
def delete_page_locator(
    page_id: str,
    locator_id: str,
    db: Session = Depends(get_db)
):
    page = crud_page.get_page(db, page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    success = crud_page.delete_page_locator(db, locator_id)
    if not success:
        raise HTTPException(status_code=404, detail="Locator not found")
    return {"message": "Locator deleted successfully"}


