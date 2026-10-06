"""
BrowserGym Automation Service for JobAutomator AI.
Uses browsergym.core and Playwright to automate LinkedIn job application flows.
"""

import sys
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BrowserGymService")

try:
    import browsergym.core
    from playwright.async_api import async_playwright
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    sys.exit(1)


class BrowserGymAutomationService:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

    async def execute_job_application(
        self,
        job_url: str,
        applicant_data: Dict[str, Any],
        pdf_resume_path: Optional[str] = None,
        session_cookies: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Automates navigating to a job posting and attempting candidacy submittal.
        """
        logger.info(f"Initiating automation for job URL: {job_url}")
        result = {
            "status": "pending",
            "job_url": job_url,
            "resume_pdf": pdf_resume_path,
            "screenshot_path": None,
            "error_reason": None
        }

        async with async_playwright() as p:
            # Launch Chromium browser with Playwright
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )

            # Restore cookies if provided
            if session_cookies:
                await context.add_cookies(session_cookies)

            page = await context.new_page()

            try:
                # 1. Navigate to Job URL
                logger.info(f"Navigating to {job_url}...")
                await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Capture initial state screenshot
                screenshot_filename = f"job_apply_{int(asyncio.get_event_loop().time())}.png"
                screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
                await page.screenshot(path=screenshot_path)
                result["screenshot_path"] = screenshot_path

                # 2. Check for Easy Apply / Candidatura Fácil button
                apply_button = await page.query_selector("button.jobs-apply-button, button:has-text('Candidatura fácil'), button:has-text('Easy Apply')")
                
                if not apply_button:
                    logger.warning("No 'Easy Apply' button detected on page.")
                    result["status"] = "requires_manual"
                    result["error_reason"] = "Botão 'Candidatura fácil' não encontrado ou vaga externa."
                    await browser.close()
                    return result

                logger.info("Clicking Easy Apply button...")
                await apply_button.click()
                await asyncio.sleep(2)

                # 3. Handle File Input if PDF resume provided
                if pdf_resume_path and os.path.exists(pdf_resume_path):
                    file_input = await page.query_selector("input[type='file']")
                    if file_input:
                        logger.info(f"Uploading ATS Resume PDF: {pdf_resume_path}")
                        await file_input.set_input_files(pdf_resume_path)
                        await asyncio.sleep(1)

                # Capture state after click & upload
                await page.screenshot(path=screenshot_path)

                result["status"] = "in_progress"
                logger.info("Application modal opened and PDF resume attached successfully.")

            except Exception as e:
                logger.error(f"Error during job application execution: {e}")
                result["status"] = "failed"
                result["error_reason"] = str(e)
            finally:
                await browser.close()

        return result


async def main():
    """
    CLI runner for testing the BrowserGym service directly.
    """
    logger.info("Running BrowserGymAutomationService test...")
    service = BrowserGymAutomationService(headless=True)
    
    # Test URL (sample public page or target job link)
    test_url = "https://www.linkedin.com/jobs/search/?keywords=Developer"
    test_applicant = {
        "full_name": "Developer Teste",
        "email": "dev@example.com",
        "phone": "+5511999999999",
        "years_experience": 5
    }

    res = await service.execute_job_application(test_url, test_applicant)
    print("\n--- Execution Result ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
