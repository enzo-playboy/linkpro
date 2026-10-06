# Project Rules & Architecture - JobAutomator AI

## Project Overview
JobAutomator AI is a reactive, multi-agent platform for automated LinkedIn job searching, ATS resume tailoring, and auto-applying using **AgentScope Java**, **BrowserGym (Python)**, and **Supabase (PostgreSQL)**.

## Core Rules & Architecture Guidelines

### 1. Reactive Agent Execution (AgentScope Java)
- All Java agent logic MUST be strictly non-blocking using **Project Reactor** (`Mono` and `Flux`).
- **NEVER** call `.block()` inside agent execution handlers or reactive pipelines.
- Always use `Mono.onErrorResume()` or `Mono.onErrorReturn()` for resilient fallback handling.
- Use `System.getenv()` for all API keys (`OPENAI_API_KEY`, `SUPABASE_KEY`, etc.).

### 2. BrowserGym Automation Service (Python)
- The Python BrowserGym runner must execute within the `.venv` virtual environment (Python 3.11).
- Use `browsergym.core` and Playwright for high-level browser actions.
- Sessions must preserve cookies safely and sanitize storage state.
- Screenshots of submittals must be uploaded to Supabase Storage buckets.

### 3. Database & Spec Integrity (Supabase + SDD)
- Database tables: `users`, `job_postings`, `resumes`, `applications`, `browser_sessions`.
- All features must trace back to the specification document `specs/prd-linkedin-job-automator.md`.
