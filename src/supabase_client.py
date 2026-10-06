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

if __name__ == "__main__":
    service = SupabaseService()
    if service.check_connection():
        print("[OK] Supabase esta conectado e funcionando com sucesso!")
    else:
        print("[WARNING] Supabase nao esta conectado. Forneca a SUPABASE_URL e a SUPABASE_KEY no arquivo .env.")

