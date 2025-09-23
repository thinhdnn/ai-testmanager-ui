from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ReleaseBase(BaseModel):
    name: str = Field(..., description="Release name")
    version: str = Field(..., description="Release version (e.g. 'v1.2.0')")
    description: Optional[str] = None
    start_date: datetime = Field(..., description="Release start date")
    end_date: Optional[datetime] = None
    status: str = Field(default="planning", description="Release status (planning, in_progress, testing, released)")


class ReleaseCreate(ReleaseBase):
    project_id: UUID = Field(..., description="Project ID")
    created_by: Optional[str] = None


class ReleaseUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None


class Release(ReleaseBase):
    id: UUID
    project_id: UUID
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============ RELEASE TEST CASE SCHEMAS ============

class ReleaseTestCaseBase(BaseModel):
    release_id: UUID
    test_case_id: UUID
    version: str = Field(..., description="Test case version for this release")


class ReleaseTestCaseCreate(ReleaseTestCaseBase):
    created_by: Optional[str] = None


class ReleaseTestCaseUpdate(BaseModel):
    version: Optional[str] = None
    updated_by: Optional[str] = None


class ReleaseTestCase(ReleaseTestCaseBase):
    id: UUID
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============ EXTENDED SCHEMAS WITH RELATIONSHIPS ============

class ReleaseWithTestCases(Release):
    """Release with included test cases"""
    test_cases: List[ReleaseTestCase] = []


class ReleaseTestCaseWithDetails(ReleaseTestCase):
    """ReleaseTestCase with test case details"""
    test_case_name: Optional[str] = None
    test_case_status: Optional[str] = None


class ReleaseStats(BaseModel):
    """Release statistics"""
    total_test_cases: int = 0
    test_cases_by_status: dict = Field(default_factory=dict)
    release_progress: float = 0.0  # percentage


class ReleaseSummary(Release):
    """Release with basic statistics"""
    stats: ReleaseStats
    author_name: Optional[str] = None 