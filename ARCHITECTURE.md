# JobAutomator AI — System Architecture & Infrastructure

> **Primary Documentation:** See [`docs/infrastructure-design.md`](docs/infrastructure-design.md) for the full architectural specification, sequence flows, database ER diagrams, security model, and deployment configurations.

---

## 🏗️ High-Level Infrastructure

![JobAutomator AI Infrastructure Blueprint](docs/assets/infra_architecture_diagram.jpg)

### Key Architectural Pillars

1. **Reactive Multi-Agent Core (Java 21 / AgentScope):**
   - **Non-blocking Reactive Streams:** All agent coordination runs strictly on **Project Reactor** (`Mono` / `Flux`).
   - **Zero Block Policy:** Blocking thread calls (`.block()`) are eliminated to prevent event-loop starvation.
   - **Centralized Error Redaction:** `CentralizedErrorHandler` redacts API keys (`sk-***`, Bearer tokens) and routes failures through non-blocking fallbacks.
   - **Token Bucket Rate Limiting:** `ReactiveRateLimiter` enforces granular rate controls per service (`LINKEDIN`, `BROWSERGYM_APPLY`, `OPENAI_API`, `GMAIL_MONITOR`).

2. **Secure Subprocess Execution Bridge:**
   - `SecureProcessExecutor` and `ProcessSanitizer` isolate Python scripts, preventing path traversal (`..`) and command injection.
   - Strict execution whitelisting for scripts under `src/`.
   - Process watchdog enforcing 120-second hard timeouts.

3. **Automation & AI Layer (Python 3.11):**
   - **BrowserGym & Playwright:** Headless automation of LinkedIn Easy Apply flows, form completion, and screenshot audits.
   - **AI Resume & ATS Optimization:** GPT-4o / Claude 3.5 Sonnet prompt chaining for tailored resumes, cover letters, and profile gap scanning.

4. **Persistence & Cloud Storage (Supabase):**
   - **PostgreSQL 15+:** Strict relational schemas with Row Level Security (RLS) for `users`, `job_postings`, `resumes`, `applications`, `browser_sessions`, and `email_notifications`.
   - **Supabase Storage:** Buckets for tailored PDF resumes (`resumes/`) and application verification proofs (`screenshots/`).

5. **Real-time Recruiter Alerts:**
   - **Gmail Monitor:** Continuous polling of recruiter responses via Gmail API.
   - **Instant Push Alerts:** Immediate alerts sent to the candidate's phone via Telegram Bot and WhatsApp Cloud API upon receiving interview invitations.

---

## 🧪 Automated Test Verification

| Test Suite | Framework | Count | Status |
| :--- | :--- | :--- | :--- |
| **Java Reactive & Security Suite** | JUnit 5, Mockito, StepVerifier | 38 | ✅ PASS |
| **Python Backend & Parsing Suite** | Python `unittest` | 9 | ✅ PASS |
| **Total Automated Tests** | | **47** | **100% Pass** |

Run tests locally:
```bash
# Java Reactive Test Suite
./mvnw.cmd test

# Python Test Suite
.venv\Scripts\python.exe -m unittest discover tests
```
