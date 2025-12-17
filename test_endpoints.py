import requests
import json

BASE_URL = "http://localhost:8002/v1"
TOKEN = "dev-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def test():
    print("1. Listing jobs...")
    resp = requests.get(f"{BASE_URL}/jobs?page_size=1", headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    
    if not data["jobs"]:
        print("No jobs found to test!")
        return

    job_id = data["jobs"][0]["id"]
    print(f"Found job ID: {job_id}")

    print("2. Getting single job details...")
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=HEADERS)
    resp.raise_for_status()
    print("Job title:", resp.json()["title"])

    print("3. Updating job status to 'reviewed'...")
    resp = requests.put(f"{BASE_URL}/jobs/{job_id}/status", 
                       headers=HEADERS, 
                       json={"status": "reviewed"})
    resp.raise_for_status()
    print("Update response:", resp.json())

    print("4. Verifying update...")
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=HEADERS)
    resp.raise_for_status()
    new_status = resp.json()["status"]
    print(f"New status: {new_status}")
    
    if new_status == "reviewed":
        print("SUCCESS! All endpoints tested.")
    else:
        print(f"FAILED: Status is {new_status}, expected 'reviewed'")

if __name__ == "__main__":
    test()
