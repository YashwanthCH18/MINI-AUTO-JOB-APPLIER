"""
Job Fetcher Stack - API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID
import math

from app.auth import get_current_user, CurrentUser
from app.database import db_service
from app.services.job_fetcher_service import job_fetcher_service
from app.models import (
    SyncJobsRequest, SyncJobsResponse, UpdateJobStatusRequest,
    FetchedJobResponse, FetchedJobListResponse,
    FetchRunResponse, FetchRunListResponse,
    JobStatusUpdateResponse, JobStatus, Portal
)

router = APIRouter(prefix="/v1", tags=["Job Fetcher"])


# ============================================
# Job Fetcher Endpoints
# ============================================

@router.post("/job-fetcher/sync", response_model=SyncJobsResponse)
async def sync_jobs(
    request: SyncJobsRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Start a job fetching operation.
    Triggers the Apify LinkedIn scraper and stores results in the database.
    """
    try:
        # Use LinkedIn as default portal for now
        portal = "linkedin"
        
        run_record = await job_fetcher_service.start_fetch(
            user_id=current_user.user_id,
            portal=portal,
            title=request.title,
            location=request.location,
            company_names=request.company_names,
            rows=request.rows
        )
        
        return SyncJobsResponse(
            run_id=run_record["id"],
            status="started",
            message=f"Job fetch started for {portal}. Check /v1/job-fetcher/runs for status."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-fetcher/sync-from-dataset")
async def sync_from_dataset(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Fetch jobs from an existing Apify dataset.
    Useful for testing without triggering a new scrape.
    """
    try:
        result = await job_fetcher_service.fetch_from_existing_dataset(
            user_id=current_user.user_id,
            dataset_id=dataset_id,
            portal="linkedin"
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-fetcher/runs", response_model=FetchRunListResponse)
async def get_fetch_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    portal: Optional[str] = None,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get paginated list of job fetch runs for the current user.
    """
    runs, total = await db_service.get_fetch_runs(
        user_id=current_user.user_id,
        portal=portal,
        status=status,
        page=page,
        page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return FetchRunListResponse(
        runs=[FetchRunResponse(**run) for run in runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# ============================================
# Jobs Endpoints
# ============================================

@router.get("/jobs", response_model=FetchedJobListResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    portal: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    q: Optional[str] = None,
    location: Optional[str] = None,
    min_lpa: Optional[float] = None,
    company: Optional[str] = None,
    sort: str = Query("fetched_at", regex="^(fetched_at|match_score|posted_at|title|company)$"),
    sort_desc: bool = True,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get paginated list of fetched jobs for the current user.
    Supports filtering by portal, status, location, company, and search query.
    """
    jobs, total = await db_service.get_jobs(
        user_id=current_user.user_id,
        portal=portal,
        status=status,
        location=location,
        min_lpa=min_lpa,
        company=company,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
        sort_desc=sort_desc
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return FetchedJobListResponse(
        jobs=[FetchedJobResponse(**job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/jobs/{job_id}", response_model=FetchedJobResponse)
async def get_job(
    job_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a single job by ID.
    """
    job = await db_service.get_job_by_id(
        user_id=current_user.user_id,
        job_id=str(job_id)
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return FetchedJobResponse(**job)


@router.put("/jobs/{job_id}/status", response_model=JobStatusUpdateResponse)
async def update_job_status(
    job_id: UUID,
    request: UpdateJobStatusRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update the status of a job (reviewed, queued, skipped).
    """
    # Validate status - users can only set certain statuses
    allowed_statuses = [JobStatus.REVIEWED, JobStatus.QUEUED, JobStatus.SKIPPED]
    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Status must be one of: {[s.value for s in allowed_statuses]}"
        )
    
    job = await db_service.update_job_status(
        user_id=current_user.user_id,
        job_id=str(job_id),
        status=request.status
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusUpdateResponse(
        id=job["id"],
        status=request.status,
        message="Status updated successfully"
    )


# ============================================
# Health Check
# ============================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "job-fetcher-stack"}
