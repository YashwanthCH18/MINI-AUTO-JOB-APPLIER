# Job Fetcher Stack - API Documentation

Base URL (Production): `https://us91gapn47.execute-api.ap-south-1.amazonaws.com/Prod/v1`
Base URL (Local): `http://localhost:8000/v1`

Authentication: All secured endpoints require `Authorization: Bearer <jwt-token>` header.

---

## 1. Start Live Job Sync
**Endpoint:** `POST /job-fetcher/sync`
**Purpose:** Triggers the Apify LinkedIn Scraper to fetch fresh jobs based on your criteria. This consumes Apify credits.

**Request Body (JSON):**
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Job title keywords | `"Software Engineer"` |
| `location` | string | Target location | `"United States"` |
| `rows` | integer | Number of jobs to fetch | `50` |
| `companyName` | array[str] | One or more company names (Optional) | `["Google", "Microsoft"]` |
| `companyId` | array[str] | LinkedIn Company IDs (Optional) | `["12345", "67890"]` |
| `publishedAt` | string | Time filter code (Optional) | `"r604800"` (Past Week) |

**Response (200 OK):**
```json
{
  "run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "started",
  "message": "Job fetch started for linkedin..."
}
```

---

## 2. Sync from Existing Dataset
**Endpoint:** `POST /job-fetcher/sync-from-dataset`
**Purpose:** Imports jobs from a previously completed Apify run (Dataset). Useful for testing or re-importing without spending credits.

**Query Parameters:**
- `dataset_id` (required): The ID of the Apify dataset (e.g., `LKHZTbW2M1zJ2pggn`).

**Response (200 OK):**
```json
{
  "run_id": "3fa85f64...",
  "jobs_found": 50,
  "new_jobs_added": 12,
  "status": "completed"
}
```

---

## 3. List Fetch Runs
**Endpoint:** `GET /job-fetcher/runs`
**Purpose:** View the history of your job fetch operations (logs).

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response (200 OK):**
```json
{
  "runs": [
    {
      "id": "3fa85f64...",
      "portal": "linkedin",
      "status": "completed",
      "started_at": "2024-01-01T10:00:00Z",
      "finished_at": "2024-01-01T10:05:00Z",
      "jobs_found": 50,
      "new_jobs_added": 12
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

## 4. List Jobs (Job Feed)
**Endpoint:** `GET /jobs`
**Purpose:** View fetched jobs stored in your database.

**Query Parameters:**
- `page`: default 1
- `page_size`: default 20
- `status`: Filter by status (e.g., `new`, `reviewed`, `skipped`)
- `sort`: `fetched_at` (default), `posted_at`, `match_score`
- `q`: Search query (title or company)

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "id": "3fa85f64...",
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "job_url": "https://linkedin.com/jobs/view/...",
      "status": "new",
      "published_at": "2024-01-01",
      "fetched_at": "2024-01-02T10:00:00Z"
    }
  ],
  "total": 100
}
```

---

## 5. Get Job Details
**Endpoint:** `GET /jobs/{job_id}`
**Purpose:** Get full details for a single job including description and application links.

**Path Parameters:**
- `job_id`: UUID of the job.

**Response (200 OK):**
```json
{
  "id": "3fa85f64...",
  "title": "Software Engineer",
  "description": "Full job description text...",
  "apply_url": "https://...",
  "salary_text": "$100k - $150k",
  ...
}
```

---

## 6. Update Job Status
**Endpoint:** `PUT /jobs/{job_id}/status`
**Purpose:** Move a job through your workflow (e.g., from `new` to `reviewed`).

**Path Parameters:**
- `job_id`: UUID of the job.

**Request Body (JSON):**
```json
{
  "status": "reviewed"
}
```
*Allowed statuses: `reviewed`, `queued`, `skipped`*

**Response (200 OK):**
```json
{
  "id": "3fa85f64...",
  "status": "reviewed",
  "message": "Status updated successfully"
}
```

---

## 7. Health Check
**Endpoint:** `GET /health`
**Purpose:** Verify service is running.
**Auth:** Not required.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "job-fetcher-stack"
}
```
