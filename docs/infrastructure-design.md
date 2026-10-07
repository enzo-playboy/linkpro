# Architecture & Infrastructure Design — JobAutomator AI

> **Status:** Production Specification & Architectural Blueprint  
> **Version:** 2.0.0  
> **Last Updated:** 2026-10-07  
> **Related Specifications:** [PRD LinkedIn Job Automator](../specs/prd-linkedin-job-automator.md) · [Database Schema](../specs/schema.sql)

---

## 1. Executive Summary

**JobAutomator AI** is a distributed, reactive multi-agent platform designed to automate the full lifecycle of LinkedIn job searching, ATS resume optimization, automated application submission, and real-time candidate notifications.

The infrastructure combines:
1. **AgentScope Java 21 (Reactive Core):** Event-driven, non-blocking agent orchestration built on **Project Reactor** (`Mono`/`Flux`), enforcing zero-blocking execution threads and resilient fallbacks.
2. **BrowserGym & Playwright (Python 3.11 Automation Layer):** Sandboxed browser environment for complex DOM navigation, dynamic form filling, LinkedIn Easy Apply execution, and visual screenshot audits.
3. **Supabase Cloud Infrastructure:** PostgreSQL 15+ relational database with Row Level Security (RLS), Supabase Storage buckets for PDFs and application evidence screenshots, and real-time triggers.
4. **Real-time Alerting Layer:** Gmail API ingestion coupled with LLM classification for immediate push alerts through Telegram Bot and WhatsApp Cloud API.
5. **Defense-in-Depth Security:** Token-bucket rate limiting, strict process sanitization against command injection and path traversal, and centralized secret masking.

---

## 2. High-Level Architecture Diagram

![JobAutomator AI Infrastructure Blueprint](assets/infra_architecture_diagram.jpg)

```mermaid
flowchart TB
    subgraph Client["Candidate & External Interfaces"]
        User["Candidate"]
        TelegramApp["Telegram Messenger"]
        WhatsAppApp["WhatsApp Mobile"]
        LinkedInPortal["LinkedIn Platform"]
    end

    subgraph CoreEngine["Reactive Orchestrator Layer (Java 21 / AgentScope)"]
        Orchestrator["JobAutomatorOrchestrator\n(Project Reactor Flux/Mono)"]
        ProfileScanner["LinkedInProfileScannerAgent\n(Profile SEO & Gap Analysis)"]
        GmailMonitor["GmailMonitorAgent\n(Email Ingestion & Classification)"]
        RateLimiter["ReactiveRateLimiter\n(Token Bucket Algorithmic Guard)"]
        ErrorHandler["CentralizedErrorHandler\n(Secret Masking & Resilient Fallbacks)"]
        SecureBridge["SecureProcessExecutor & ProcessSanitizer\n(Anti-Traversal & Subprocess Isolation)"]
    end

    subgraph PythonWorker["Python 3.11 Automation & AI Layer"]
        AIService["ai_service.py\n(ATS Matching & Cover Letter Generator)"]
        BrowserGym["browsergym_service.py\n(Playwright Engine + Session Store)"]
        TaxonomyEngine["industry_taxonomy.py\n(Domain & Skill Taxonomies)"]
        PDFGenerator["pdf_generator.py\n(ReportLab ATS PDF Engine)"]
    end

    subgraph DataCloud["Supabase Infrastructure & Persistence"]
        PostgresDB[("PostgreSQL 15+\n(RLS, UUIDs, Foreign Keys)")]
        StorageBuckets[("Supabase Storage\n(resumes/ & screenshots/)")]
        AuthService["Supabase Auth Engine"]
    end

    subgraph ExternalAPIs["External SaaS & LLM Providers"]
        OpenAI["OpenAI API / LLMs\n(GPT-4o / Claude 3.5 Sonnet)"]
        GmailAPI["Google Workspace / Gmail API\n(OAuth2 Token Exchange)"]
        TelegramAPI["Telegram Bot API\n(https://api.telegram.org)"]
    end

    %% Interactions
    User -->|Configures Preferences| Orchestrator
    Orchestrator --> RateLimiter
    RateLimiter -->|Allow Token| Orchestrator
    Orchestrator -->|Evaluate Profile| ProfileScanner
    ProfileScanner -->|Inference Query| OpenAI
    Orchestrator -->|Non-blocking Exec| SecureBridge
    SecureBridge -->|Sanitized Subprocess| BrowserGym
    SecureBridge -->|Sanitized Subprocess| AIService

    BrowserGym -->|Headless Browser Actions| LinkedInPortal
    BrowserGym -->|Audit Screenshots| StorageBuckets
    BrowserGym -->|Update Application Status| PostgresDB

    AIService -->|LLM Structured Extraction| OpenAI
    AIService -->|Compile Resume Document| PDFGenerator
    PDFGenerator -->|Upload Generated PDF| StorageBuckets

    GmailMonitor -->|Polls Unread Messages| GmailAPI
    GmailMonitor -->|Categorize Email Intent| OpenAI
    GmailMonitor -->|Urgent Interview Detected| TelegramAPI
    TelegramAPI -->|Push Alert| TelegramApp

    Orchestrator -.->|Error Interception & Masking| ErrorHandler
    ErrorHandler -.->|Safe Error Telemetry| PostgresDB
```

---

## 3. Core Component Topologies

### 3.1 Reactive Java Orchestrator (AgentScope Core)

The orchestrator coordinates agent lifecycles using strict **asynchronous non-blocking reactive streams**:
- **Project Reactor Pipelines:** Workloads are modeled as `Flux<Map<String, Object>>` without thread starvation. **`.block()` is prohibited** across all execution paths.
- **Fail-Safe Fallbacks:** Every external API or subprocess call wraps in `Mono.onErrorResume()` with `CentralizedErrorHandler.formatErrorResponse()`.
- **Token Bucket Rate Limiter (`ReactiveRateLimiter`):** Prevents IP blocks and API quota exhaustion with independent per-service tokens:
  - `LINKEDIN`: 5 requests / min (burst capacity 2)
  - `BROWSERGYM_APPLY`: 2 submissions / min (burst capacity 1)
  - `OPENAI_API`: 60 requests / min (burst capacity 10)
  - `GMAIL_MONITOR`: 12 polls / min (burst capacity 3)

### 3.2 Secure Subprocess Execution Bridge

Communication between the Java orchestrator and Python agents occurs via an audited subprocess interface:

```mermaid
sequenceDiagram
    autonumber
    participant Orch as JobAutomatorOrchestrator
    participant Guard as ProcessSanitizer
    participant Exec as SecureProcessExecutor
    participant Py as Python Runtime (.venv)
    participant Cloud as Supabase / Web

    Orch->>Guard: validateScriptPath("src/browsergym_service.py")
    alt Path contains ".." or illegal character
        Guard-->>Orch: Throws SecurityValidationException
    else Valid Whitelisted Script
        Guard-->>Exec: Sanitized Path + Args
        Exec->>Exec: Cleanse Environment (mask secrets)
        Exec->>Py: ProcessBuilder.start() (with 120s Timeout)
        Py->>Cloud: Performs BrowserGym automation
        Py-->>Exec: Exit Code + STDOUT / STDERR
        Exec-->>Orch: ProcessExecutionResult(exitCode, stdout, stderr)
    end
```

**Security Controls Enforced:**
- **Path Traversal Shield:** Rejection of `..`, `\`, and paths resolving outside the workspace root.
- **Whitelist Enforcement:** Only scripts residing in `src/` and ending in `.py` can be executed.
- **Shell Injection Immunity:** Arguments are passed as discrete token arrays directly to OS syscalls without invoking `sh` or `cmd.exe` interpreters.
- **Hard Timeout Enforcement:** Long-running browser processes are terminated after 120 seconds to prevent zombie processes.

---

## 4. Data Layer Architecture (Supabase / PostgreSQL)

### 4.1 Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ JOB_POSTINGS : discovers
    USERS ||--o{ RESUMES : owns
    USERS ||--o{ APPLICATIONS : submits
    USERS ||--o{ BROWSER_SESSIONS : maintains
    USERS ||--o{ EMAIL_NOTIFICATIONS : receives

    USERS {
        uuid id PK
        string email UK
        string full_name
        jsonb master_resume_json
        jsonb preferences_json
        timestamp created_at
    }

    JOB_POSTINGS {
        uuid id PK
        string platform
        string external_job_id
        string title
        string company
        string location
        string work_mode
        text description_raw
        jsonb requirements_extracted
        float match_score
        string apply_url
        boolean is_easy_apply
        timestamp created_at
    }

    RESUMES {
        uuid id PK
        uuid user_id FK
        uuid job_id FK
        text tailored_resume_text
        text cover_letter_text
        jsonb keywords_matched
        timestamp created_at
    }

    APPLICATIONS {
        uuid id PK
        uuid user_id FK
        uuid job_id FK
        uuid resume_id FK
        string status
        text failure_reason
        string screenshot_url
        timestamp applied_at
        timestamp created_at
    }

    BROWSER_SESSIONS {
        uuid id PK
        uuid user_id FK
        text cookies_encrypted
        string user_agent
        string status
        timestamp updated_at
    }

    EMAIL_NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        string company_name
        string email_subject
        string classification
        text summary
        boolean sent_to_telegram
        boolean sent_to_whatsapp
        timestamp created_at
    }
```

### 4.2 Storage Buckets & Policies

1. **`resumes` Bucket (Private / Authenticated):**
   - Path convention: `resumes/{user_id}/{job_id}_tailored.pdf`
   - Purpose: Stores dynamically rendered ATS-compliant PDF resumes and cover letters.
2. **`screenshots` Bucket (Audit Trail):**
   - Path convention: `screenshots/{user_id}/{application_id}_submitted.png`
   - Purpose: Captures high-resolution browser proof at the final submission step before closing Playwright.

---

## 5. End-to-End Pipeline Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant Cand as Candidate
    participant Java as Orchestrator (Java 21)
    participant Rate as Token Bucket RateLimiter
    participant PyAI as AI Service (Python)
    participant LLM as OpenAI GPT-4o
    participant Gym as BrowserGym Runner
    participant Supa as Supabase (DB & Storage)
    participant Mail as Gmail Monitor
    participant TG as Telegram Bot

    Note over Java,Gym: Phase 1: Search, Match & Tailor
    Java->>Rate: acquire(ServiceName.LINKEDIN)
    Rate-->>Java: Token granted
    Java->>PyAI: Extract & Score Job Postings
    PyAI->>LLM: Compute ATS Score (0-100)
    LLM-->>PyAI: Match Score: 88.0% + Extracted Keywords
    PyAI->>Supa: Save to job_postings table

    alt Score >= 75.0 Threshold
        Java->>Rate: acquire(ServiceName.OPENAI_API)
        Rate-->>Java: Token granted
        Java->>PyAI: Generate Tailored Cover Letter & Resume
        PyAI->>LLM: Generate Tailored Content
        LLM-->>PyAI: Tailored Markdown / PDF Content
        PyAI->>Supa: Upload PDF to resumes/ bucket & insert resumes row

        Note over Java,Gym: Phase 2: Autonomous Submission
        Java->>Rate: acquire(ServiceName.BROWSERGYM_APPLY)
        Rate-->>Java: Token granted
        Java->>Gym: Execute Easy Apply (Headless Playwright)
        Gym->>Gym: Fill forms, upload PDF, capture screenshot
        Gym->>Supa: Upload screenshot & update applications (SUBMITTED)
    end

    Note over Mail,TG: Phase 3: Recruiter Feedback & Instant Alerting
    Mail->>Mail: Poll unread recruitment emails
    Mail->>LLM: Classify intent (INTERVIEW_INVITE / REJECTION / STATUS)
    alt Intent == INTERVIEW_INVITE
        Mail->>TG: Send high-priority alert with action link
        TG-->>Cand: 🚨 Urgent Telegram Notification Delivered
        Mail->>Supa: Record email_notifications (sent_to_telegram = true)
    end
```

---

## 6. Security & Hardening Boundaries

| Boundary | Threat Vector | Mitigation Strategy |
| :--- | :--- | :--- |
| **Credential Management** | Leaked API keys or database passwords | Zero hardcoded credentials. All secrets injected via `System.getenv()` / `os.getenv()`. Centralized regex scrubbing in `CentralizedErrorHandler` masks `sk-***`, tokens, and passwords. |
| **Subprocess Ingestion** | Remote Code Execution (RCE) / Path Traversal | `ProcessSanitizer` enforces script whitelisting (`src/`), rejects `..`, and forbids command chain characters (`;&|`$><`). |
| **Anti-Bot / LinkedIn Ban** | Rapid request bursts triggering Captcha | `ReactiveRateLimiter` enforces Token Bucket throttling with randomised jitter intervals and humanized browser velocity. |
| **Database Access** | Multi-tenant data leakage | Supabase Row Level Security (RLS) enabled on all tables (`users`, `job_postings`, `resumes`, `applications`, `browser_sessions`). |
| **Session Cookies** | Session hijacking | LinkedIn session cookies encrypted before storing into `browser_sessions` and stripped from client-facing payloads. |

---

## 7. Deployment Models

### 7.1 Hybrid Local Development (Current Setup)
- **Host OS:** Windows / Linux / macOS
- **Java Runtime:** OpenJDK 21 LTS with Maven Wrapper (`./mvnw.cmd` / `./mvnw`)
- **Python Environment:** Isolated `.venv` virtual environment (Python 3.11 with Playwright Chromium binaries)
- **Database:** Supabase Cloud managed instance via connection pooler

### 7.2 Production Containerized Architecture (Docker & Cloud Run / ECS)

```mermaid
graph LR
    subgraph ContainerA["Container 1: Orchestrator Service"]
        direction TB
        JVM["OpenJDK 21 Alpine"]
        AgentScopeApp["JobAutomator Java App"]
        JVM --- AgentScopeApp
    end

    subgraph ContainerB["Container 2: Python Automation Worker"]
        direction TB
        PyEnv["Python 3.11-slim"]
        PlaywrightBin["Chromium & BrowserGym Dependencies"]
        WorkerAPI["FastAPI / AI Worker Daemon"]
        PyEnv --- PlaywrightBin
        PlaywrightBin --- WorkerAPI
    end

    subgraph CloudInfra["Managed Cloud Services"]
        SupaDB[("Supabase Managed PostgreSQL")]
        S3Storage[("Supabase Object Storage")]
        SecretMgr["Cloud Secret Manager"]
    end

    ContainerA <-->|gRPC / REST (Internal)| ContainerB
    ContainerA -->|JDBC / SSL| SupaDB
    ContainerB -->|HTTPS SDK| S3Storage
    SecretMgr -.->|Inject ENV| ContainerA
    SecretMgr -.->|Inject ENV| ContainerB
```

---

## 8. Verification & Test Architecture

The infrastructure includes complete automated test suites validating reliability:

1. **Reactive Stream Integrity (`StepVerifier`):**
   - Non-blocking execution verified across `JobAutomatorOrchestratorTest`.
   - Error handling tested with simulated 500 errors and OpenAI rate limits.
2. **Security & Sanitization Testing (`ProcessSanitizerTest`):**
   - 10 test scenarios ensuring path traversal (`../../etc/passwd`), metacharacters, and unapproved scripts fail immediately.
3. **Rate Limiting Simulation (`ReactiveRateLimiterTest`):**
   - Token exhaustion and refill verification under high concurrent loads.
4. **Backend Python Test Suite (`tests/test_backend.py`):**
   - Validation of resume parsing, scoring heuristics, and taxonomy extraction.

Total Test Suite Coverage: **47 automated tests** (38 Java + 9 Python) with 100% pass rate.
