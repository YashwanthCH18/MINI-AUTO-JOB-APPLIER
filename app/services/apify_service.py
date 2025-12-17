"""
Job Fetcher Stack - Apify LinkedIn Service
"""
import httpx
from typing import List, Optional
from app.config import get_settings
from app.models import ApifyJobResult
import asyncio


class ApifyService:
    """Service for interacting with Apify LinkedIn Jobs Scraper."""
    
    BASE_URL = "https://api.apify.com/v2"
    
    def __init__(self):
        self.settings = get_settings()
        self.token = self.settings.apify_api_token
        self.actor_id = self.settings.apify_actor_id
    
    async def run_linkedin_scraper(
        self,
        title: Optional[str] = None,
        location: Optional[str] = None,
        company_names: Optional[List[str]] = None,
        rows: int = 50
    ) -> dict:
        """
        Start the LinkedIn Jobs Scraper actor.
        Returns the run info including run_id.
        """
        # Build input payload
        input_data = {
            "rows": rows,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            }
        }
        
        if title:
            input_data["title"] = title
        if location:
            input_data["location"] = location
        if company_names:
            input_data["companyName"] = company_names
        
        # Start the actor
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/acts/{self.actor_id}/runs",
                params={"token": self.token},
                json=input_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_run_status(self, run_id: str) -> dict:
        """Get the status of an actor run."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/actor-runs/{run_id}",
                params={"token": self.token}
            )
            response.raise_for_status()
            return response.json()
    
    async def wait_for_run_completion(
        self, 
        run_id: str, 
        poll_interval: int = 5,
        max_wait: int = 300
    ) -> dict:
        """
        Poll until the run is complete.
        Returns the final run status.
        """
        elapsed = 0
        while elapsed < max_wait:
            status = await self.get_run_status(run_id)
            run_status = status.get("data", {}).get("status")
            
            if run_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                return status
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(f"Run {run_id} did not complete within {max_wait} seconds")
    
    async def get_run_results(self, run_id: str) -> List[ApifyJobResult]:
        """
        Get the results from a completed run.
        Returns list of parsed job results.
        """
        # First get the run info to find the dataset ID
        run_info = await self.get_run_status(run_id)
        dataset_id = run_info.get("data", {}).get("defaultDatasetId")
        
        if not dataset_id:
            raise ValueError(f"No dataset found for run {run_id}")
        
        # Fetch results from the dataset
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/datasets/{dataset_id}/items",
                params={"token": self.token}
            )
            response.raise_for_status()
            raw_results = response.json()
        
        # Parse into our model
        jobs = []
        for item in raw_results:
            try:
                job = ApifyJobResult(**item)
                jobs.append(job)
            except Exception as e:
                # Log but don't fail on individual parse errors
                print(f"Failed to parse job: {e}")
                continue
        
        return jobs
    
    async def fetch_jobs_sync(
        self,
        title: Optional[str] = None,
        location: Optional[str] = None,
        company_names: Optional[List[str]] = None,
        rows: int = 50
    ) -> List[ApifyJobResult]:
        """
        Run the scraper and wait for results.
        This is the main method to use for synchronous fetching.
        """
        # Start the run
        run_info = await self.run_linkedin_scraper(
            title=title,
            location=location,
            company_names=company_names,
            rows=rows
        )
        
        run_id = run_info.get("data", {}).get("id")
        if not run_id:
            raise ValueError("Failed to start Apify actor run")
        
        # Wait for completion
        await self.wait_for_run_completion(run_id)
        
        # Get results
        return await self.get_run_results(run_id)
    
    async def get_dataset_results_direct(self, dataset_id: str) -> List[ApifyJobResult]:
        """
        Get results directly from a known dataset ID.
        Useful for testing with existing datasets.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/datasets/{dataset_id}/items",
                params={"token": self.token}
            )
            response.raise_for_status()
            raw_results = response.json()
        
        jobs = []
        for item in raw_results:
            try:
                job = ApifyJobResult(**item)
                jobs.append(job)
            except Exception as e:
                print(f"Failed to parse job: {e}")
                continue
        
        return jobs


# Singleton instance
apify_service = ApifyService()
