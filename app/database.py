"""
Job Fetcher Stack - Database Service
"""
from supabase import create_client, Client
from app.config import get_settings
from app.models import (
    FetchRunStatus, JobStatus, FetchedJobResponse, 
    FetchRunResponse, ApifyJobResult
)
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
import math


class DatabaseService:
    """Service for database operations using Supabase."""
    
    def __init__(self):
        settings = get_settings()
        # Use service key for backend operations (bypasses RLS)
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    # ============================================
    # Job Fetch Runs
    # ============================================
    
    async def create_fetch_run(
        self, 
        user_id: str, 
        portal: str,
        input_params: dict
    ) -> dict:
        """Create a new fetch run record."""
        result = self.client.table("job_fetch_runs").insert({
            "user_id": user_id,
            "portal": portal,
            "status": FetchRunStatus.RUNNING.value,
            "input_params": input_params
        }).execute()
        return result.data[0] if result.data else None
    
    async def update_fetch_run(
        self,
        run_id: str,
        status: FetchRunStatus,
        jobs_found: int = 0,
        new_jobs_added: int = 0,
        errors_json: dict = None
    ) -> dict:
        """Update a fetch run with results."""
        update_data = {
            "status": status.value,
            "jobs_found": jobs_found,
            "new_jobs_added": new_jobs_added,
            "finished_at": datetime.utcnow().isoformat()
        }
        if errors_json:
            update_data["errors_json"] = errors_json
            
        result = self.client.table("job_fetch_runs").update(
            update_data
        ).eq("id", run_id).execute()
        return result.data[0] if result.data else None
    
    async def get_fetch_runs(
        self,
        user_id: str,
        portal: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """Get paginated fetch runs for a user."""
        query = self.client.table("job_fetch_runs").select(
            "*", count="exact"
        ).eq("user_id", user_id)
        
        if portal:
            query = query.eq("portal", portal)
        if status:
            query = query.eq("status", status)
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.order("started_at", desc=True).range(offset, offset + page_size - 1)
        
        result = query.execute()
        return result.data, result.count or 0
    
    # ============================================
    # Fetched Jobs
    # ============================================
    
    async def upsert_job(
        self,
        user_id: str,
        fetch_run_id: str,
        job_data: ApifyJobResult,
        portal: str = "linkedin"
    ) -> Tuple[dict, bool]:
        """
        Insert or update a job. Returns (job_record, is_new).
        Uses external_job_id + user_id + portal as unique key.
        """
        # Extract job ID from LinkedIn URL
        external_job_id = self._extract_linkedin_job_id(job_data.jobUrl)
        
        # Parse salary
        lpa_min, lpa_max = self._parse_salary(job_data.salary)
        
        # Parse published date
        posted_at = None
        if job_data.publishedAt:
            try:
                posted_at = job_data.publishedAt
            except:
                pass
        
        job_record = {
            "user_id": user_id,
            "fetch_run_id": fetch_run_id,
            "portal": portal,
            "external_job_id": external_job_id,
            "title": job_data.title,
            "company": job_data.companyName,
            "company_id": job_data.companyId,
            "company_url": job_data.companyUrl,
            "location": job_data.location,
            "lpa_min": lpa_min,
            "lpa_max": lpa_max,
            "salary_text": job_data.salary,
            "job_url": job_data.jobUrl,
            "apply_url": job_data.applyUrl,
            "apply_type": job_data.applyType,
            "description": job_data.description,
            "contract_type": job_data.contractType,
            "experience_level": job_data.experienceLevel,
            "work_type": job_data.workType,
            "sector": job_data.sector,
            "benefits": job_data.benefits,
            "applications_count": job_data.applicationsCount,
            "posted_at": posted_at,
            "posted_time_text": job_data.postedTime,
        }
        
        # Check if job already exists
        existing = self.client.table("fetched_jobs").select("id").eq(
            "user_id", user_id
        ).eq("portal", portal).eq("external_job_id", external_job_id).execute()
        
        if existing.data:
            # Update existing (but don't change status)
            job_record.pop("user_id")  # Don't update user_id
            result = self.client.table("fetched_jobs").update(
                job_record
            ).eq("id", existing.data[0]["id"]).execute()
            return result.data[0] if result.data else None, False
        else:
            # Insert new
            result = self.client.table("fetched_jobs").insert(job_record).execute()
            return result.data[0] if result.data else None, True
    
    async def get_jobs(
        self,
        user_id: str,
        portal: Optional[List[str]] = None,
        status: Optional[List[str]] = None,
        location: Optional[str] = None,
        min_lpa: Optional[float] = None,
        company: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "fetched_at",
        sort_desc: bool = True
    ) -> Tuple[List[dict], int]:
        """Get paginated jobs for a user."""
        query = self.client.table("fetched_jobs").select(
            "*", count="exact"
        ).eq("user_id", user_id)
        
        if portal:
            query = query.in_("portal", portal)
        if status:
            query = query.in_("status", status)
        if location:
            query = query.ilike("location", f"%{location}%")
        if min_lpa:
            query = query.gte("lpa_min", min_lpa)
        if company:
            query = query.ilike("company", f"%{company}%")
        if q:
            # Search in title or company
            query = query.or_(f"title.ilike.%{q}%,company.ilike.%{q}%")
        
        # Sorting
        query = query.order(sort, desc=sort_desc)
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        result = query.execute()
        return result.data, result.count or 0
    
    async def get_job_by_id(self, user_id: str, job_id: str) -> Optional[dict]:
        """Get a single job by ID."""
        result = self.client.table("fetched_jobs").select("*").eq(
            "id", job_id
        ).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    
    async def update_job_status(
        self, 
        user_id: str, 
        job_id: str, 
        status: JobStatus
    ) -> Optional[dict]:
        """Update job status."""
        result = self.client.table("fetched_jobs").update({
            "status": status.value
        }).eq("id", job_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None
    
    # ============================================
    # Helper Methods
    # ============================================
    
    def _extract_linkedin_job_id(self, job_url: str) -> str:
        """Extract job ID from LinkedIn URL."""
        # URL format: https://www.linkedin.com/jobs/view/{job_id}?...
        try:
            if "/jobs/view/" in job_url:
                # Get the part after /view/
                parts = job_url.split("/jobs/view/")[1]
                # Remove query params and trailing parts
                job_id = parts.split("?")[0].split("-")[-1]
                return job_id
        except:
            pass
        return job_url  # Fallback to full URL
    
    def _parse_salary(self, salary_text: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """Parse salary text into min/max values (in LPA for India, or yearly for US)."""
        if not salary_text:
            return None, None
        
        try:
            # Handle US format: $69,000.00/yr - $96,500.00/yr
            if "$" in salary_text:
                import re
                numbers = re.findall(r'\$([\d,]+(?:\.\d+)?)', salary_text)
                if len(numbers) >= 2:
                    min_val = float(numbers[0].replace(",", "")) / 100000  # Convert to Lakhs
                    max_val = float(numbers[1].replace(",", "")) / 100000
                    return min_val, max_val
                elif len(numbers) == 1:
                    val = float(numbers[0].replace(",", "")) / 100000
                    return val, val
        except:
            pass
        
        return None, None


# Singleton instance
db_service = DatabaseService()
