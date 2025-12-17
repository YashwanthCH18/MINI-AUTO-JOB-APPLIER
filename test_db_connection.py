from app.database import db_service
import asyncio

async def test_connection():
    try:
        print("Testing DB connection...")
        # Try to select from job_fetch_runs
        result = db_service.client.table("job_fetch_runs").select("*").limit(1).execute()
        print("Success! Data:", result.data)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())
