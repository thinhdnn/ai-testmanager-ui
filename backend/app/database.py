from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .config import settings

# Create base class for models
Base = declarative_base()

# Lazy database connection - only created when needed
_engine = None
_async_engine = None
_SessionLocal = None
_AsyncSessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url)
    return _engine

def get_async_engine():
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=True,
        )
    return _async_engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_async_session_local():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = sessionmaker(
            get_async_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSessionLocal

# Dependency to get database session
def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


# Dependency to get async database session
async def get_async_session() -> AsyncSession:
    async with get_async_session_local()() as session:
        yield session 