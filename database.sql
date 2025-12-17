-- ============================================
-- Job Fetcher Stack - Database Tables
-- Run this in Supabase SQL Editor
-- ============================================

-- Table: job_fetch_runs
-- Tracks each job fetching operation
CREATE TABLE public.job_fetch_runs (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    portal text NOT NULL DEFAULT 'linkedin',
    status text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    started_at timestamp with time zone DEFAULT now(),
    finished_at timestamp with time zone,
    jobs_found integer DEFAULT 0,
    new_jobs_added integer DEFAULT 0,
    errors_json jsonb,
    input_params jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT job_fetch_runs_pkey PRIMARY KEY (id),
    CONSTRAINT job_fetch_runs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Table: fetched_jobs
-- Stores all jobs fetched from portals
CREATE TABLE public.fetched_jobs (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    fetch_run_id uuid,
    portal text NOT NULL DEFAULT 'linkedin',
    external_job_id text,
    title text NOT NULL,
    company text NOT NULL,
    company_id text,
    company_url text,
    location text,
    lpa_min numeric,
    lpa_max numeric,
    salary_text text,
    job_url text NOT NULL,
    apply_url text,
    apply_type text,
    description text,
    requirements_snippet text,
    contract_type text,
    experience_level text,
    work_type text,
    sector text,
    benefits text,
    applications_count text,
    posted_at date,
    posted_time_text text,
    fetched_at timestamp with time zone DEFAULT now(),
    match_score integer DEFAULT 0,
    status text NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'queued', 'applied', 'skipped', 'expired')),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT fetched_jobs_pkey PRIMARY KEY (id),
    CONSTRAINT fetched_jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT fetched_jobs_fetch_run_id_fkey FOREIGN KEY (fetch_run_id) REFERENCES public.job_fetch_runs(id) ON DELETE SET NULL,
    CONSTRAINT fetched_jobs_unique_job UNIQUE (user_id, portal, external_job_id)
);

-- Indexes for better query performance
CREATE INDEX idx_fetched_jobs_user_id ON public.fetched_jobs(user_id);
CREATE INDEX idx_fetched_jobs_status ON public.fetched_jobs(status);
CREATE INDEX idx_fetched_jobs_portal ON public.fetched_jobs(portal);
CREATE INDEX idx_fetched_jobs_fetched_at ON public.fetched_jobs(fetched_at DESC);
CREATE INDEX idx_fetched_jobs_match_score ON public.fetched_jobs(match_score DESC);
CREATE INDEX idx_job_fetch_runs_user_id ON public.job_fetch_runs(user_id);
CREATE INDEX idx_job_fetch_runs_status ON public.job_fetch_runs(status);

-- Enable Row Level Security
ALTER TABLE public.job_fetch_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fetched_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for job_fetch_runs
CREATE POLICY "Users can view their own fetch runs"
    ON public.job_fetch_runs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own fetch runs"
    ON public.job_fetch_runs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own fetch runs"
    ON public.job_fetch_runs FOR UPDATE
    USING (auth.uid() = user_id);

-- RLS Policies for fetched_jobs
CREATE POLICY "Users can view their own fetched jobs"
    ON public.fetched_jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own fetched jobs"
    ON public.fetched_jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own fetched jobs"
    ON public.fetched_jobs FOR UPDATE
    USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for fetched_jobs updated_at
CREATE TRIGGER update_fetched_jobs_updated_at
    BEFORE UPDATE ON public.fetched_jobs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();
