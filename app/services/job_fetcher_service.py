"""
Job Fetcher Stack - Job Fetcher Service
Orchestrates the job fetching process.
"""
from typing import Optional, List
from uuid import UUID
from app.services.apify_service import apify_service
from app.database import db_service
from app.models import FetchRunStatus, ApifyJobResult
import asyncio


class JobFetcherService:
    """Service for orchestrating job fetching operations."""
    
    async def start_fetch(
        self,
        user_id: str,
        portal: str = "linkedin",
        title: Optional[str] = None,
        location: Optional[str] = None,
        company_names: Optional[List[str]] = None,
        company_ids: Optional[List[str]] = None,
        published_at: Optional[str] = None,
        rows: int = 50
    ) -> dict:
        """
        Start a job fetching operation.
        Creates a fetch run record and starts the Apify scraper.
        """
        # Create fetch run record
        input_params = {
            "title": title,
            "location": location,
            "company_names": company_names,
            "company_ids": company_ids,
            "published_at": published_at,
            "rows": rows
        }
        
        run_record = await db_service.create_fetch_run(
            user_id=user_id,
            portal=portal,
            input_params=input_params
        )
        
        if not run_record:
            raise Exception("Failed to create fetch run record")
        
        run_id = run_record["id"]
        
        # Start background task for fetching
        # In Lambda, we'll need to handle this differently (Step Functions, SQS, etc.)
        asyncio.create_task(
            self._execute_fetch(
                run_id=run_id,
                user_id=user_id,
                title=title,
                location=location,
                company_names=company_names,
                company_ids=company_ids,
                published_at=published_at,
                rows=rows
            )
        )
        
        return run_record
    
    async def _execute_fetch(
        self,
        run_id: str,
        user_id: str,
        title: Optional[str] = None,
        location: Optional[str] = None,
        company_names: Optional[List[str]] = None,
        company_ids: Optional[List[str]] = None,
        published_at: Optional[str] = None,
        rows: int = 50
    ):
        """
        Execute the actual job fetching in the background.
        This runs the Apify scraper and stores results in the database.
        """
        try:
            # Fetch jobs from Apify
            jobs = await apify_service.fetch_jobs_sync(
                title=title,
                location=location,
                company_names=company_names,
                company_ids=company_ids,
                published_at=published_at,
                rows=rows
            )
            
            # Store jobs in database
            new_jobs_count = 0
            for job in jobs:
                _, is_new = await db_service.upsert_job(
                    user_id=user_id,
                    fetch_run_id=run_id,
                    job_data=job,
                    portal="linkedin"
                )
                if is_new:
                    new_jobs_count += 1
            
            # Update fetch run as completed
            await db_service.update_fetch_run(
                run_id=run_id,
                status=FetchRunStatus.COMPLETED,
                jobs_found=len(jobs),
                new_jobs_added=new_jobs_count
            )
            
        except Exception as e:
            # Update fetch run as failed
            await db_service.update_fetch_run(
                run_id=run_id,
                status=FetchRunStatus.FAILED,
                errors_json={"error": str(e)}
            )
            raise
    
    async def fetch_from_existing_dataset(
        self,
        user_id: str,
        dataset_id: str,
        portal: str = "linkedin"
    ) -> dict:
        """
        Fetch jobs from an existing Apify dataset.
        Useful for testing without running a new scrape.
        """
        # Create fetch run record
        input_params = {
            "dataset_id": dataset_id,
            "source": "existing_dataset"
        }
        
        run_record = await db_service.create_fetch_run(
            user_id=user_id,
            portal=portal,
            input_params=input_params
        )
        
        run_id = run_record["id"]
        
        try:
            # Get jobs from existing dataset
            jobs = await apify_service.get_dataset_results_direct(dataset_id)
            
            # Store jobs in database
            new_jobs_count = 0
            for job in jobs:
                _, is_new = await db_service.upsert_job(
                    user_id=user_id,
                    fetch_run_id=run_id,
                    job_data=job,
                    portal=portal
                )
                if is_new:
                    new_jobs_count += 1
            
            # Update fetch run as completed
            await db_service.update_fetch_run(
                run_id=run_id,
                status=FetchRunStatus.COMPLETED,
                jobs_found=len(jobs),
                new_jobs_added=new_jobs_count
            )
            
            return {
                "run_id": run_id,
                "jobs_found": len(jobs),
                "new_jobs_added": new_jobs_count,
                "status": "completed"
            }
            
        except Exception as e:
            await db_service.update_fetch_run(
                run_id=run_id,
                status=FetchRunStatus.FAILED,
                errors_json={"error": str(e)}
            )
            raise


# Singleton instance
job_fetcher_service = JobFetcherService()
