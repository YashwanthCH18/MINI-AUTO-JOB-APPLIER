

# AI Career Automation Platform — Full Multi-Stack Doc (in the example style)

I am building an AI-powered career growth and job automation platform. Frontend is Next.js with shadcn/ui. Backend is Python FastAPI on AWS Lambda (SAM). Database is Supabase (Postgres + Auth + Storage). LLM is Gemini (user-provided key). I split the backend into multiple stacks deployed separately in the same AWS account. The stacks are: **Auth & Identity Stack**, **Onboarding Profile Stack**, **Integrations Stack**, **GitHub Projects Stack**, **Resume & Documents Stack**, **Identity & Document Verification Stack**, **Job Fetcher Stack**, **Job Application Stack**, **Insights & Reports Stack**, **Notifications Stack**, **API Management Stack**, and **Admin Stack**.

First the user lands on the landing page, then taps Get Started → auth. Supabase issues a JWT stored in the browser. The frontend includes `Authorization: Bearer <JWT>` for all requests to the backend stacks. All stacks validate the JWT and enforce user/admin scopes.

Below is the full flow, then each stack with endpoints, inputs, outputs, and integrations.

# Frontend Flow

- Landing `/`
  - CTA: Get Started → `/auth`
  - Learn more scroll

- Auth `/auth`
  - Tabs: Sign In | Create Account
  - OAuth: Google/GitHub/LinkedIn
  - New users → `/onboarding`
  - Existing users → `/dashboard`

- Onboarding `/onboarding`
  - Profile: name, email, LinkedIn, GitHub username
  - Career prefs: roles, min target LPA, preferred locations
  - Integrations: connect GitHub; enter Gemini key; optional LinkedIn/Naukri/Indeed/Gmail tokens
  - Review & Finish → `/dashboard`

- Dashboard `/dashboard`
  - Cards: job search status, verified certificates, projects count, resume versions, skill gap alerts
  - Quick actions → Projects/Reports/Job Control

- Projects `/projects`
  - Synced repos list
  - AI description regenerate
  - Record/Upload 20–30s project intro video
  - Notification when new repo detected

- Resumes `/resumes`
  - AI Resume builder (limit 5–10)
  - Auto-update when new repo detected
  - Generate → Preview → Download PDF
  - Certificates tab: upload, statuses (Pending/Verified/Rejected)

- Job Control `/job-control`
  - Toggles: Start/Stop job search, Auto-apply on/off
  - Portals select: LinkedIn/Naukri/Indeed
  - Filters: Role/Location/Min LPA/Company type
  - Save & Activate

- Reports `/reports`
  - Applications chart
  - Resume performance
  - Skill gap analytics
  - Export CSV/PDF
  - Email schedule: daily/weekly

- Notifications `/notifications`
  - Repo detected, cert results, skill gaps, resume updates, job apply summaries
  - Mark read/unread, deep-links

- Settings `/settings`
  - Career Preferences
  - API Keys & Tokens
  - GitHub reconnect
  - Notifications & Privacy
  - Account (logout/delete/re-run onboarding)

- Admin `/admin/*`
  - Login → Dashboard
  - Users, Control, Notifications, API Management, Reports
  - Certificate verification under `/admin/users/:userid/certificates`

# Supabase Auth and Profile

- Using Supabase default auth.
- Fields we reference:
  - uid, display_name, email, providers, provider_type, created_at, last_sign_in_at
  - We don’t use phone.
- JWT is added by frontend to all backend requests.
- Profiles table:
  - id (uuid=uid), email, display_name, role (user|admin), github_username, created_at, last_sign_in_at

# Stacks

## 1) **Auth & Identity Stack**

- Purpose
  - JWT validation (Supabase JWKS/secret), role resolution, session introspection.
- Endpoints
  - GET `/v1/auth/session`
    - Input: Authorization header (JWT)
    - Output: { user_id, role, email, display_name, issued_at, expires_at }
- Integration
  - Middleware shared library for all stacks to validate JWT and extract `user_id`, `role`.

## 2) **Onboarding Profile Stack**

- Purpose
  - Textual onboarding data and user preferences (not tokens).
- Tables
  - `onboarding`: id, user_id, roles_targeted text[], min_target_lpa numeric, preferred_locations text[], github_username, completed bool, created_at, updated_at
  - `job_settings`: id, user_id, search_active bool, auto_apply bool, portals text[], roles text[], locations text[], min_lpa numeric, company_types text[], updated_at
- Endpoints (user-scoped)
  - GET `/v1/onboarding`
    - Output: onboarding record (scoped to jwt.sub)
  - PUT `/v1/onboarding`
    - Input: { roles_targeted[], min_target_lpa, preferred_locations[], github_username, completed }
    - Output: updated onboarding
  - GET `/v1/settings/job`
    - Output: job_settings
  - PUT `/v1/settings/job`
    - Input: { search_active, auto_apply, portals[], roles[], locations[], min_lpa, company_types[] }
    - Output: updated job_settings
- Integration
  - Emits `user.onboarding.completed` used by other stacks (e.g., Reports for welcome email).

## 3) **Integrations Stack**

- Purpose
  - OAuth and user tokens (GitHub, LinkedIn, Naukri, Indeed, Gmail, Gemini). Stores encrypted user-level tokens.
- Tables
  - `user_integrations`: id, user_id, provider enum, status, external_user_id, scopes, connected_at, revoked_at
  - `api_tokens`: id, user_id, provider, token_encrypted, expires_at, last_used_at
- Endpoints (user-scoped)
  - GET `/v1/integrations`
    - Output: list of providers with status
  - POST `/v1/integrations/github/connect`
    - Output: { auth_url }
  - GET `/v1/integrations/github/callback`
    - Input: code
    - Output: { status: "connected" }
  - POST `/v1/integrations/tokens`
    - Input: { provider, token, expires_at? } (Gemini, LinkedIn, Naukri, Indeed, Gmail)
    - Output: { status: "saved" }
  - DELETE `/v1/integrations/:provider`
    - Output: { status: "revoked" }
- Integration
  - Provides secure token retrieval to other stacks (internal service-to-service).
  - Emits `integrations.github.connected` which triggers repo sync in **GitHub Projects Stack**.

## 4) **GitHub Projects Stack**

- Purpose
  - Sync user repositories, generate AI descriptions, manage per-project intro videos (record/upload), and emit repo events.
- Tables
  - `repositories`: id, user_id, provider_repo_id, name, html_url, description_ai, default_branch, last_synced_at, has_intro_video bool
  - `project_videos`: id, user_id, repo_id, storage_path, status (uploaded|transcoded|failed), duration_sec, created_at
- Endpoints (user-scoped)
  - POST `/v1/projects/sync`
    - Uses user’s GitHub token via **Integrations Stack** to sync repos
    - Output: { synced_count }
  - GET `/v1/projects`
    - Query: page, page_size, q
    - Output: repo list with AI description and video status
  - POST `/v1/projects/:id/describe`
    - Input: { regenerate: bool }
    - Output: { description_ai }
  - POST `/v1/projects/:id/video/signed-url`
    - Input: { content_type, size }
    - Output: { upload_url, storage_path }
  - GET `/v1/projects/:id/video`
    - Output: { status, playback_url? }
- Integration
  - Emits `repo.detected`, `repo.updated`, `project_video.uploaded`
  - Consumed by **Resume & Documents Stack** for auto resume updates

## 5) **Resume & Documents Stack**

- Purpose
  - AI resume builder, resume versions, PDF generation, document storage helpers (excluding KYC/cert verification which is separate).
- Tables
  - `resumes`: id, user_id, role_type, name, active_version_id, auto_tailor_enabled bool, created_at, updated_at
  - `resume_versions`: id, resume_id, content_json, pdf_storage_path, created_at, generated_from enum, source_repo_ids text[]
- Endpoints (user-scoped)
  - GET `/v1/resumes`
    - Output: list of resumes with counts
  - POST `/v1/resumes`
    - Input: { name, role_type }
    - Output: created resume
  - POST `/v1/resumes/:id/build`
    - Input: { mode: "ai", instructions?, tailor_for_role? }
    - Output: { version_id, preview_html? }
  - GET `/v1/resumes/:id/download`
    - Output: { file_url, expires_at }
  - PUT `/v1/resumes/:id/auto-tailor`
    - Input: { enabled: bool }
    - Output: { enabled }
- Integration
  - Consumes `repo.detected` / `repo.updated` to optionally auto-generate new resume versions and set `source_repo_ids`.
  - References project intro videos by `repo_id` for embedding (iframe URL retrieved from **GitHub Projects Stack** when needed).

## 6) **Identity & Document Verification Stack**

- Purpose
  - Government ID/KYC and certificates verification in one place with admin review workflow.
- Tables
  - `certificates`: id, user_id, document_type, storage_path, ocr_extract_json, status (pending|verified|rejected), rejection_notes, uploaded_at, reviewed_by_admin_id, reviewed_at
- Endpoints
  - User
    - POST `/v1/certificates`
      - Input: { document_type }
      - Output: { upload_url, storage_path, certificate_id }
    - GET `/v1/certificates`
      - Output: list { id, document_type, status, uploaded_at }
  - Admin (admin role)
    - GET `/v1/admin/users/:user_id/certificates`
      - Output: list with OCR extracts and status
    - POST `/v1/admin/certificates/:id/approve`
      - Output: { status: "verified" }
    - POST `/v1/admin/certificates/:id/reject`
      - Input: { notes }
      - Output: { status: "rejected" }
- Integration
  - OCR async job on upload; updates `ocr_extract_json`.
  - Emits `certificate.status.changed` → **Notifications Stack**.
  - Future: KYC provider webhooks can update status similarly.

## 7) **Job Fetcher Stack**

- Purpose
  - Fetch/scrape jobs from portals (LinkedIn, Naukri, Indeed), store in Supabase, provide job listings for user review. Runs on a configurable cron schedule.
- Tables
  - `job_fetch_runs`: id, user_id, portal, status (running|completed|failed), started_at, finished_at, jobs_found, new_jobs_added, errors_json
  - `fetched_jobs`: id, user_id, portal, external_job_id, title, company, location, lpa_min, lpa_max, job_url, description_snippet, requirements_snippet, posted_at, fetched_at, match_score, status (new|reviewed|queued|applied|skipped|expired)
- Endpoints (user-scoped)
  - POST `/v1/job-fetcher/sync`
    - Input: { portals[]? } (defaults to user's enabled portals from job_settings)
    - Output: { run_id, status: "started" }
  - GET `/v1/job-fetcher/runs`
    - Query: page, page_size, portal, status, from, to
    - Output: fetch run history
  - GET `/v1/jobs`
    - Query: page, page_size, portal[], status[], q, location, min_lpa, company, from, to, sort
    - Output: list of fetched jobs with pagination
  - GET `/v1/jobs/:id`
    - Output: full job details
  - PUT `/v1/jobs/:id/status`
    - Input: { status: "reviewed"|"queued"|"skipped" }
    - Output: { status }
- Cron Job
  - Configurable schedule (default: every 6 hours)
  - For each user with `search_active=true` in job_settings:
    - Fetches jobs from enabled portals using user filters
    - Stores new jobs, skips duplicates (by external_job_id)
    - Calculates match_score based on user preferences
    - Emits `jobs.fetched` event
- Integration
  - Uses user tokens from **Integrations Stack**.
  - Uses platform keys from **API Management Stack**.
  - Reads filters from **Onboarding Profile Stack** (`job_settings`).
  - Emits `jobs.fetched` → **Notifications Stack** ("X new jobs found!").

## 8) **Job Application Stack**

- Purpose
  - Apply to fetched jobs (auto or manual), track application status and employer responses.
- Tables
  - `job_applications`: id, user_id, fetched_job_id (FK to fetched_jobs), portal, resume_version_id, cover_letter_text, status (pending|submitted|failed), response_status (pending|viewed|shortlisted|rejected|interview|offer), applied_at, error_json, updated_at
  - `job_apply_runs`: id, user_id, mode (auto|manual|batch), status (running|completed|failed), started_at, finished_at, total_applied, total_failed, errors_json
- Endpoints (user-scoped)
  - POST `/v1/job-apply/activate`
    - Input: { auto_apply: bool }
    - Output: { auto_apply, status: "activated"|"deactivated" }
  - POST `/v1/job-apply/single/:job_id`
    - Input: { resume_id?, cover_letter? }
    - Output: { application_id, status }
  - POST `/v1/job-apply/batch`
    - Input: { job_ids[], resume_id? }
    - Output: { run_id, status: "started", queued_count }
  - GET `/v1/job-apply/runs`
    - Query: page, page_size, mode, status, from, to
    - Output: application run history
  - GET `/v1/job-apply/applications`
    - Query: page, page_size, portal[], status[], response_status[], from, to, q, sort
    - Output: list of applications with job details
  - GET `/v1/job-apply/applications/:id`
    - Output: full application details
  - PUT `/v1/job-apply/applications/:id/response`
    - Input: { response_status: "viewed"|"shortlisted"|"rejected"|"interview"|"offer" }
    - Output: { response_status }
- Admin Control (admin role)
  - POST `/v1/admin/job-apply/user/:user_id`
    - Input: { pause: bool }
    - Output: { status: "paused"|"resumed" }
  - POST `/v1/admin/job-apply/emergency-stop`
    - Input: { enabled: bool }
    - Output: { enabled }
  - GET `/v1/admin/job-apply/runs`
    - Query: page, page_size, user_id[], mode, status, from, to
    - Output: all application runs across users
  - GET `/v1/admin/job-apply/applications`
    - Query: page, page_size, user_id[], portal[], status[], response_status[], from, to, q, sort
    - Output: all applications across users
- Integration
  - Reads from `fetched_jobs` table (Job Fetcher Stack).
  - Uses user tokens from **Integrations Stack**.
  - Uses platform keys from **API Management Stack**.
  - Calls **Resume & Documents Stack** for resume selection/tailoring.
  - Emits `job.applied`, `job.apply.summary` → **Notifications Stack**.
  - Application data consumed by **Insights & Reports Stack**.

## 9) **Insights & Reports Stack**

- Purpose
  - Single source for both user and admin dashboards/reports. User endpoints auto-scope to `jwt.sub`. Admin endpoints require `role=admin` and allow wide filters.
- Tables (read/compute)
  - `analytics_daily` plus cross-table reads to `job_applications`, `job_apply_runs`, `fetched_jobs`, `job_fetch_runs`, `resumes`, `resume_versions`, `skill_gaps`, `repositories`, `certificates`, `profiles`, `job_settings`
- User Endpoints
  - GET `/v1/dashboard/summary`
    - Output: cards { job_search_status, verified_certificates_count, projects_synced_count, resume_versions_count, resume_limit, skill_gap_alerts_count, top_skill_gaps[], applications_7d, applications_by_portal_7d[] }
  - GET `/v1/reports/applications/series` (from, to, interval, portal[])
    - Output: time series
  - GET `/v1/reports/applications/summary` (from, to, portal[])
    - Output: totals and breakdowns
  - GET `/v1/reports/resume-performance` (from, to, resume_id[])
    - Output: per-resume usage/success
  - GET `/v1/insights/skill-gaps` (severity[], from, to, q, page, page_size)
    - Output: skill gaps
  - GET `/v1/reports/exports` (type, from, to, format)
    - Output: { file_url, expires_at }
  - POST `/v1/reports/email/subscription`
    - Input: { schedule: daily|weekly|off }
    - Output: { status: "updated" }
- Admin Endpoints (admin role)
  - GET `/v1/admin/dashboard/summary`
    - Output: platform metrics (total_users, active_job_searches, pending_certificates, api_key_expiry_alerts, applications_24h, top_portals_7d[], errors_24h)
  - GET `/v1/admin/reports/applications/series` (from, to, interval, user_id[], portal[], role, location[], min_lpa_from, min_lpa_to)
  - GET `/v1/admin/reports/applications/list` (q, portal[], user_id[], status[], response_status[], from, to, page, page_size, sort)
  - GET `/v1/admin/reports/resume-performance` (from, to, user_id[], resume_id[], role_type[])
  - GET `/v1/admin/reports/certificates/stats` (from, to, status[], user_id[])
  - GET `/v1/admin/reports/users` (q, search_active, github_linked, from, to, page, page_size, sort)
  - GET `/v1/admin/reports/exports` (type, filters…, format)
- Integration
  - Nightly aggregation jobs fill `analytics_daily`.
  - Pulls `api_key` expiry info from **API Management Stack** for admin cards.
  - Sends scheduled report emails via **Notifications Stack** (or SES directly).

## 10) **Notifications Stack**

- Purpose
  - Central notifications (in-app, email/push) and user read states.
- Tables
  - `notifications`: id, user_id, type, payload_json, read, link_url, created_at
- Endpoints
  - GET `/v1/notifications` (page, page_size, type?, read?)
    - Output: list of notifications
  - PUT `/v1/notifications/:id/read`
    - Output: { read: true }
- Integration
  - Consumes events: `repo.detected`, `certificate.status.changed`, `jobs.fetched`, `job.applied`, `job.apply.summary`, `report.ready`
  - Sends email via provider; honors user preferences in Settings.

## 11) **API Management Stack**

- Purpose
  - Admin-only platform keys for unofficial APIs (LinkedIn/Naukri/Indeed scrapers, Apify actors, etc.). Rotations, masking, expiry reminders, audits.
- Tables
  - `platform_api_keys`: id, service, key_encrypted, masked_suffix, expiry_at, last_rotated_at, status, updated_by_admin_id
- Admin Endpoints
  - GET `/v1/admin/api-management`
    - Output: list of services with masked key and expiry
  - PUT `/v1/admin/api-management/:service`
    - Input: { key, expiry_at? }
    - Output: { status: "updated", masked_suffix, expiry_at }
- Integration
  - **Job Fetcher Stack** and **Job Application Stack** fetch service keys securely server-to-server.
  - Emits `api_key.expiry_warning` to **Notifications Stack** (admin recipients).

## 12) **Admin Stack**

- Purpose
  - Admin UI orchestration: users list, cross-domain navigation, pass-through to domain admin endpoints, control toggles.
- Endpoints
  - GET `/v1/admin/users` (q, page, page_size, sort)
    - Output: list with summary fields (email, display_name, created_at, job_search_status, verified_docs_count, github_linked, applications_7d)
  - POST `/v1/admin/job-apply/user/:user_id` (pause/resume) → proxies to **Job Application Stack**
  - POST `/v1/admin/job-apply/emergency-stop` → proxies to **Job Application Stack**
  - GET `/v1/admin/users/:user_id/certificates` → proxies to **Identity & Document Verification Stack**
  - POST `/v1/admin/notifications` (broadcast) → **Notifications Stack**
  - GET `/v1/admin/dashboard` → aggregates from **Insights & Reports Stack** and **API Management Stack**
- Integration
  - Thin orchestrator. Real admin authority and writes happen in domain stacks with admin checks.

# Cross-Stack Integrations (Events and Calls)

- **Integrations → GitHub Projects**
  - `integrations.github.connected` or manual `/projects/sync` triggers repo sync.
- **GitHub Projects → Resume & Documents**
  - `repo.detected`, `repo.updated`, `project_video.uploaded` → resume auto-update and video embedding references.
- **Identity & Document Verification → Notifications**
  - `certificate.status.changed` → user notification.
- **Job Fetcher → Notifications**
  - `jobs.fetched` → user notification ("X new jobs found matching your criteria").
- **Job Fetcher → Job Application**
  - Provides `fetched_jobs` table that Job Application reads from for applying.
- **Job Application → Notifications + Insights**
  - `job.applied`, `job.apply.summary` → user notifications.
  - Applications written to DB, consumed by Insights & Reports.
- **API Management → Job Fetcher + Job Application**
  - Platform keys available to both stacks for portal connectors; expiry warnings go to admin notifications.
- **Insights & Reports → Notifications**
  - Scheduled report emails (daily/weekly) sent via Notifications.

# Security and JWT

- All endpoints require JWT. User endpoints ignore any `user_id` in query (auto-scope to `jwt.sub`). Admin endpoints require `role=admin`.
- RLS on user-owned tables; service role used in backend with explicit scoping.
- Audit log for admin actions and exports.

# Filters and Exports

- Common filters: `q`, `from`, `to`, `portal[]`, `status[]`, `user_id[]` (admin), `page`, `page_size`, `sort`.
- Exports (CSV/PDF): signed URL responses; URLs expire.

# Storage

- Supabase Storage for PDFs, certificate images, and project videos.
- Uploads via signed URLs from the owning stack:
  - Project videos → **GitHub Projects Stack**
  - Certificates → **Identity & Document Verification Stack**
  - Resume PDFs → **Resume & Documents Stack**

# LLM and Tokens

- User must enter Gemini key in **Integrations Stack**.
- Stacks invoke Gemini under user context where needed:
  - AI repo descriptions (Projects)
  - Resume build/tailor (Resumes)
  - Skill gap analysis (Reports)
- Keys are encrypted; never exposed in full to the client after save.

# Summary

- Delivered a full multi-stack spec in the example style with all stacks, inputs, outputs, endpoints, and their integrations.
- If you want, I can generate an OpenAPI skeleton per stack and a DB index checklist next.