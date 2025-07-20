from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import fastapi_users, current_active_user, auth_backend
from ...database import get_async_session
from ...models.user import User
from ...schemas.user import UserRead, UserCreate, UserUpdate

router = APIRouter()

# Include fastapi-users routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/reset-password",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/verify",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)


@router.get("/me", response_model=UserRead)
async def get_current_user(user: User = Depends(current_active_user)):
    """Get current authenticated user"""
    return user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    """Login endpoint using OAuth2 password flow"""
    try:
        # Use fastapi-users login
        response = await fastapi_users.get_auth_router(auth_backend).routes[0].endpoint(
            form_data, session
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) 