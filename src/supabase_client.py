"""
Supabase Database Integration Client - JobAutomator AI
Handles table persistence, job tracking, resume storage, and application logging.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SupabaseClient")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

class SupabaseService:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self._init_client()

    def _init_client(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("SUPABASE_URL or SUPABASE_KEY not set in .env. Operating in disconnected/fallback mode.")
            return

        try:
            from supabase import create_client, Client
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.is_connected = True
            logger.info("Successfully connected to Supabase project at: %s", SUPABASE_URL)
        except Exception as e:
            logger.error("Failed to initialize Supabase client: %s", str(e))
            self.is_connected = False

    def check_connection(self) -> bool:
        if not self.is_connected or not self.client:
            return False
        try:
            # Query users table (limit 1) to test connectivity
            response = self.client.table("users").select("id").limit(1).execute()
            logger.info("Supabase connectivity test successful. Query response: %s", response.data)
            return True
        except Exception as e:
            logger.error("Supabase connection check failed: %s", str(e))
            return False

    def insert_user(self, email: str, full_name: str, preferences: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            logger.info("[MOCK] Insert User: email=%s, name=%s", email, full_name)
            return {"id": "mock-user-uuid", "email": email, "full_name": full_name}
        try:
            payload = {
                "email": email,
                "full_name": full_name,
                "preferences_json": preferences or {}
            }
            res = self.client.table("users").upsert(payload, on_conflict="email").execute()
            if res.data:
                logger.info("User upserted successfully: %s", res.data[0]['id'])
                return res.data[0]
        except Exception as e:
            logger.error("Error upserting user: %s", str(e))
        return None

    def insert_job_posting(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            logger.info("[MOCK] Insert Job Posting: %s at %s", job_data.get('title'), job_data.get('company'))
            return {"id": "mock-job-uuid", **job_data}
        try:
            res = self.client.table("job_postings").upsert(job_data, on_conflict="platform,external_job_id").execute()
            if res.data:
                logger.info("Job posting upserted successfully: %s", res.data[0]['id'])
                return res.data[0]
        except Exception as e:
            logger.error("Error upserting job posting: %s", str(e))
        return None

    def log_application(self, user_id: str, job_id: str, status: str, screenshot_url: Optional[str] = None, failure_reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            logger.info("[MOCK] Log Application: job_id=%s, status=%s", job_id, status)
            return {"id": "mock-app-uuid", "status": status}
        try:
            payload = {
                "user_id": user_id,
                "job_id": job_id,
                "status": status,
                "screenshot_url": screenshot_url,
                "failure_reason": failure_reason
            }
            res = self.client.table("applications").insert(payload).execute()
            if res.data:
                logger.info("Application logged: %s", res.data[0]['id'])
                return res.data[0]
        except Exception as e:
            logger.error("Error logging application: %s", str(e))
        return None

    def save_browser_session(self, user_id: Optional[str], session_data: str, user_agent: str = "Playwright-Chromium", status: str = "active") -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            logger.info("[MOCK] Save Browser Session for user: %s (status: %s)", user_id, status)
            return {"id": "mock-session-uuid", "user_id": user_id, "status": status}
        try:
            payload = {
                "user_id": user_id,
                "cookies_encrypted": session_data,
                "user_agent": user_agent,
                "status": status
            }
            res = self.client.table("browser_sessions").insert(payload).execute()
            if res.data:
                logger.info("Browser session synced to Supabase: %s", res.data[0]['id'])
                return res.data[0]
        except Exception as e:
            logger.error("Error saving browser session to Supabase: %s", str(e))
        return None

    def sync_applicant_profile(self, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        personal = profile_data.get("personal_info", {})
        email = personal.get("email", "candidato@exemplo.com")
        full_name = personal.get("full_name", "Candidato Automação")
        return self.insert_user(email=email, full_name=full_name, preferences=profile_data)

if __name__ == "__main__":
    import json
    service = SupabaseService()
    print("\n--- Teste de Conexão Supabase ---")
    if service.check_connection():
        print("[OK] Supabase conectado com sucesso na nuvem!")
        
        # 1. Sincronizar Perfil
        profile_file = os.path.join(os.getcwd(), "data", "applicant_profile.json")
        user_id = None
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                res_u = service.sync_applicant_profile(pdata)
                if res_u:
                    user_id = res_u.get("id")
                    print(f"[OK] Perfil do candidato sincronizado na tabela 'users'! (ID: {user_id})")
            except Exception as e:
                print(f"[AVISO] Falha ao sincronizar perfil: {e}")

        # 2. Sincronizar Sessão Local do LinkedIn
        session_file = os.path.join(os.getcwd(), "sessions", "linkedin_state.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    raw_session = f.read()
                res_s = service.save_browser_session(user_id=user_id, session_data=raw_session, user_agent="Playwright-Chromium")
                if res_s:
                    print(f"[OK] Sessão do LinkedIn sincronizada na tabela 'browser_sessions'! (ID: {res_s.get('id')})")
            except Exception as e:
                print(f"[AVISO] Falha ao sincronizar sessão: {e}")
        else:
            print("[INFO] Nenhuma sessão local 'sessions/linkedin_state.json' encontrada para sincronizar.")

    else:
        print("[WARNING] Não foi possível consultar a tabela 'users'.")
        print("DICA: Se você acabou de criar o projeto no Supabase, lembre-se de executar o script SQL contido em 'specs/schema.sql' no SQL Editor do painel do Supabase para criar as tabelas!")

