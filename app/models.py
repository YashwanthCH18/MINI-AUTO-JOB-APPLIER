"""
Job Fetcher Stack - Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from uuid import UUID


# ============================================
# Enums
# ============================================

class JobStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    QUEUED = "queued"
    APPLIED = "applied"
    SKIPPED = "skipped"
    EXPIRED = "expired"


class FetchRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Portal(str, Enum):
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    INDEED = "indeed"


# ============================================
# Request Models
# ============================================

class SyncJobsRequest(BaseModel):
    """Request body for POST /v1/job-fetcher/sync"""
    portals: Optional[List[Portal]] = None  # Defaults to user's enabled portals
    title: Optional[str] = None
    location: Optional[str] = None
    company_names: Optional[List[str]] = None
    rows: int = Field(default=50, ge=1, le=100)


class UpdateJobStatusRequest(BaseModel):
    """Request body for PUT /v1/jobs/:id/status"""
    status: JobStatus


# ============================================
# Response Models
# ============================================

class SyncJobsResponse(BaseModel):
    """Response for POST /v1/job-fetcher/sync"""
    run_id: UUID
    status: str = "started"
    message: str = "Job fetch started"


class FetchedJobResponse(BaseModel):
    """Single job response"""
    id: UUID
    portal: str
    external_job_id: Optional[str]
    title: str
    company: str
    company_url: Optional[str]
    location: Optional[str]
    salary_text: Optional[str]
    job_url: str
    apply_url: Optional[str]
    apply_type: Optional[str]
    description: Optional[str]
    contract_type: Optional[str]
    experience_level: Optional[str]
    work_type: Optional[str]
    sector: Optional[str]
    applications_count: Optional[str]
    posted_at: Optional[date]
    posted_time_text: Optional[str]
    fetched_at: datetime
    match_score: int
    status: JobStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FetchedJobListResponse(BaseModel):
    """Paginated list of jobs"""
    jobs: List[FetchedJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FetchRunResponse(BaseModel):
    """Single fetch run response"""
    id: UUID
    portal: str
    status: FetchRunStatus
    started_at: datetime
    finished_at: Optional[datetime]
    jobs_found: int
    new_jobs_added: int
    errors_json: Optional[dict]

    class Config:
        from_attributes = True


class FetchRunListResponse(BaseModel):
    """Paginated list of fetch runs"""
    runs: List[FetchRunResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobStatusUpdateResponse(BaseModel):
    """Response for status update"""
    id: UUID
    status: JobStatus
    message: str = "Status updated"


# ============================================
# Apify Models (matching their API response)
# ============================================

class ApifyJobResult(BaseModel):
    """Model for Apify LinkedIn job scraper output"""
    title: str
    location: Optional[str] = None
    postedTime: Optional[str] = None
    publishedAt: Optional[str] = None
    jobUrl: str
    companyName: str
    companyUrl: Optional[str] = None
    description: Optional[str] = None
    applicationsCount: Optional[str] = None
    contractType: Optional[str] = None
    experienceLevel: Optional[str] = None
    workType: Optional[str] = None
    sector: Optional[str] = None
    salary: Optional[str] = None
    companyId: Optional[str] = None
    applyUrl: Optional[str] = None
    applyType: Optional[str] = None
    benefits: Optional[str] = None
