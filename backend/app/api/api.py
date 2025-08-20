from fastapi import APIRouter
from .endpoints import users, projects, test_cases, fixtures, steps, test_results, tags, auth, pages

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(test_cases.router, prefix="/test-cases", tags=["test-cases"])
api_router.include_router(fixtures.router, prefix="/fixtures", tags=["fixtures"])
api_router.include_router(steps.router, prefix="/steps", tags=["steps"])
api_router.include_router(test_results.router, prefix="/test-results", tags=["test-results"]) 
api_router.include_router(tags.router, prefix="/tags", tags=["tags"]) 
api_router.include_router(pages.router, prefix="/pages", tags=["pages"]) 