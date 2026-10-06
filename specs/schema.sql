-- Database Schema for JobAutomator AI (Supabase / PostgreSQL)

-- 1. Table: users
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    master_resume_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    preferences_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Table: job_postings
CREATE TABLE IF NOT EXISTS public.job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL DEFAULT 'linkedin',
    external_job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    work_mode TEXT NOT NULL DEFAULT 'remote', -- remote, hybrid, on-site
    description_raw TEXT NOT NULL,
    requirements_extracted JSONB DEFAULT '{}'::jsonb,
    match_score FLOAT DEFAULT 0.0,
    apply_url TEXT NOT NULL,
    is_easy_apply BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_platform_job UNIQUE (platform, external_job_id)
);

-- 3. Table: resumes
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.job_postings(id) ON DELETE CASCADE,
    tailored_resume_text TEXT NOT NULL,
    cover_letter_text TEXT,
    keywords_matched JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Table: applications
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.job_postings(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES public.resumes(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, submitted, failed, requires_manual
    failure_reason TEXT,
    screenshot_url TEXT,
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Table: browser_sessions
CREATE TABLE IF NOT EXISTS public.browser_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    cookies_encrypted TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active', -- active, expired, captcha_blocked
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Table: email_notifications
CREATE TABLE IF NOT EXISTS public.email_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    email_subject TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT 'STATUS_UPDATE', -- INTERVIEW_INVITE, STATUS_UPDATE, REJECTION
    summary TEXT,
    sent_to_telegram BOOLEAN DEFAULT false,
    sent_to_whatsapp BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Table: linkedin_posts
CREATE TABLE IF NOT EXISTS public.linkedin_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    post_content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft', -- draft, scheduled, published
    scheduled_for TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_postings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.browser_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.linkedin_posts ENABLE ROW LEVEL SECURITY;

-- Allow public access policies for anon key development
CREATE POLICY "Allow public access to users" ON public.users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public access to job_postings" ON public.job_postings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public access to resumes" ON public.resumes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public access to applications" ON public.applications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public access to browser_sessions" ON public.browser_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public access to email_notifications" ON public.email_notifications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public access to linkedin_posts" ON public.linkedin_posts FOR ALL USING (true) WITH CHECK (true);

