from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TestResultHistoryBase(BaseModel):
    project_id: UUID  # Changed from str to UUID
    name: Optional[str] = None
    test_result_file_name: Optional[str] = None
    success: bool
    status: str
    execution_time: Optional[int] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[str] = None  # JSON string
    browser: Optional[str] = None
    video_url: Optional[str] = None


class TestResultHistoryCreate(TestResultHistoryBase):
    created_by: Optional[str] = None
    last_run_by: Optional[str] = None


class TestResultHistoryUpdate(BaseModel):
    name: Optional[str] = None
    test_result_file_name: Optional[str] = None
    success: Optional[bool] = None
    status: Optional[str] = None
    execution_time: Optional[int] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[str] = None
    browser: Optional[str] = None
    video_url: Optional[str] = None


class TestResultHistoryInDB(TestResultHistoryBase):
    id: UUID  # Changed from str to UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_run_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class TestResultHistory(TestResultHistoryInDB):
    author_name: Optional[str] = None


class TestCaseExecutionBase(BaseModel):
    test_result_id: UUID  # Changed from str to UUID
    test_case_id: UUID  # Changed from str to UUID
    status: str
    duration: Optional[int] = None
    error_message: Optional[str] = None
    output: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retries: int = 0


class TestCaseExecutionCreate(TestCaseExecutionBase):
    pass


class TestCaseExecutionUpdate(BaseModel):
    status: Optional[str] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None
    output: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retries: Optional[int] = None


class TestCaseExecutionInDB(TestCaseExecutionBase):
    id: UUID  # Changed from str to UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TestCaseExecution(TestCaseExecutionInDB):
    pass 