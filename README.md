# Job Fetcher Stack

Fetches jobs from LinkedIn (via Apify) and stores them in Supabase for the AI Career Automation Platform.

## Quick Start

### 1. Setup Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `JWT_SECRET` - Your Supabase JWT secret
- `APIFY_API_TOKEN` - Your Apify API token (already set)

### 3. Setup Database

Run the SQL in `database.sql` in your Supabase SQL Editor to create:
- `job_fetch_runs` table
- `fetched_jobs` table
- Required indexes and RLS policies

### 4. Run Locally

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for Swagger UI.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/job-fetcher/sync` | Start a job fetch from LinkedIn |
| POST | `/v1/job-fetcher/sync-from-dataset` | Import from existing Apify dataset |
| GET | `/v1/job-fetcher/runs` | List fetch run history |
| GET | `/v1/jobs` | List fetched jobs with filters |
| GET | `/v1/jobs/{id}` | Get single job details |
| PUT | `/v1/jobs/{id}/status` | Update job status |
| GET | `/v1/health` | Health check |

## Testing with Existing Dataset

You already have results in Apify. To import them without running a new scrape:

```bash
curl -X POST "http://localhost:8000/v1/job-fetcher/sync-from-dataset?dataset_id=LKHZTbW2M1zJ2pggn" \
  -H "Authorization: Bearer dev-token"
```

## Authentication

All endpoints require JWT authentication (except `/health`).

In DEV_MODE, use `dev-token` as the Bearer token for testing.

## Project Structure

```
JOB FETCHER/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── config.py        # Settings
│   ├── models.py        # Pydantic models
│   ├── routes.py        # API endpoints
│   ├── auth.py          # JWT authentication
│   ├── database.py      # Supabase operations
│   └── services/
│       ├── __init__.py
│       ├── apify_service.py      # Apify API client
│       └── job_fetcher_service.py # Orchestration
├── venv/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── database.sql
└── README.md
```

## Apify Integration

This stack uses the `bebity/linkedin-jobs-scraper` actor on Apify.

Your existing resources:
- **Actor Run**: `zfadVljMlOZ0QNSPx`
- **Dataset**: `LKHZTbW2M1zJ2pggn`
- **Key-Value Store**: `Hb5MrJm3UGlQLb3vm`
