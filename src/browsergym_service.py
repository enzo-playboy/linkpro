"""
BrowserGym Automation Service for JobAutomator AI.
Uses browsergym.core and Playwright to automate LinkedIn job application flows,
multi-step form answering (Form QA Engine), and persistent session management.
"""

import sys
import os
import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("BrowserGymService")

try:
    import browsergym.core
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    sys.exit(1)


DEFAULT_SESSION_FILE = os.path.join(os.getcwd(), "sessions", "linkedin_state.json")
DEFAULT_PROFILE_FILE = os.path.join(os.getcwd(), "data", "applicant_profile.json")


def normalize_job_url(raw_url: str) -> str:
    """
    Normalizes complex LinkedIn search/tracking URLs into clean direct view URLs.
    Example: .../jobs/search/?currentJobId=4471908581 -> https://www.linkedin.com/jobs/view/4471908581/
    """
    if not raw_url:
        return raw_url
    match = re.search(r"currentJobId=(\d+)", raw_url)
    if match:
        job_id = match.group(1)
        normalized = f"https://www.linkedin.com/jobs/view/{job_id}/"
        logger.info(f"URL de busca normalizada para visualização direta da vaga: {normalized}")
        return normalized
    return raw_url


class FormQAEngine:
    """
    Deterministic & Heuristic Question Answering Engine for LinkedIn Easy Apply forms.
    Resolves inputs, textareas, selects, and radio buttons using applicant data.
    """

    def __init__(self, applicant_profile: Dict[str, Any]):
        self.profile = applicant_profile or {}
        self.personal = self.profile.get("personal_info", {})
        self.auth = self.profile.get("work_authorization", {})
        self.exp = self.profile.get("experience", {})
        self.skills = self.exp.get("skills_years", {})
        self.languages = self.profile.get("languages", {})
        self.compensation = self.profile.get("compensation", {})
        self.defaults = self.profile.get("screening_defaults", {})

    def resolve_text_value(self, label_text: str, input_type: str = "text") -> Optional[str]:
        text = label_text.lower()

        # 1. Phone / Telefone / Teléfono / Celular / Mobile
        if input_type == "tel" or any(k in text for k in [
            "phone", "telefone", "telefono", "teléfono", "celular", "móvil", "movil",
            "mobile", "número", "numero", "contato", "contacto", "tel"
        ]):
            raw_phone = str(self.personal.get("phone", "65 99999-9999"))
            clean_phone = re.sub(r"^\+55\s*", "", raw_phone).strip()
            return clean_phone

        # 2. Email / Correo
        if any(k in text for k in ["email", "e-mail", "correo"]):
            return self.personal.get("email", "")

        # 3. City / Location / Cidade / Ciudad / Ubicación
        if any(k in text for k in [
            "city", "cidade", "ciudad", "localização", "ubicación", "location", "reside", "residencia", "localidad"
        ]):
            return self.personal.get("city", "Cuiabá, Mato Grosso, Brasil")

        # 4. Salary / Pretensão salarial / Salario / Sueldo
        if any(k in text for k in ["salary", "pretensão", "salário", "salario", "sueldo", "remuneração", "remuneración", "compensation"]):
            return str(self.compensation.get("desired_salary", "12000"))

        # 5. Notice period / Aviso prévio / Preaviso
        if any(k in text for k in ["notice period", "aviso prévio", "aviso previo", "preaviso", "start date", "semanas"]):
            if "day" in text or "dia" in text or "días" in text or "dias" in text:
                return str(self.defaults.get("notice_period_days", "15"))
            return str(self.defaults.get("notice_period_weeks", "2"))

        # 6. Specific skill experience (e.g., "How many years of work experience do you have with Java / React?")
        for skill_name, years in self.skills.items():
            if skill_name.lower() in text:
                return str(years)

        # 7. General experience in years (anos / años / years)
        if any(k in text for k in ["years of experience", "anos de experiência", "años de experiencia", "how many years", "cuántos años", "cuantos anos"]):
            return str(self.exp.get("total_years", 5))

        # 8. Numeric fallback
        if input_type == "number":
            return "3"

        return None

    def resolve_radio_selection(self, question_text: str, options: List[str]) -> Optional[str]:
        q = question_text.lower()

        # Questions where answer should be YES / SIM
        # - Legally authorized to work
        # - Willing to relocate / commute / work hybrid / onsite / presencial
        # - Comfort with background check
        positive_cues = [
            "authorized", "autorizado", "elegível", "legally", "direito de trabalhar",
            "commute", "relocate", "deslocar", "híbrido", "hybrid", "presencial", "presencialmente",
            "background check", "maior de 18", "18 years", "experiência", "experience", "disponibilidade",
            "disponível", "carteira", "cnh", "viagem", "viajar"
        ]
        if any(cue in q for cue in positive_cues):
            for opt in options:
                if opt.lower().strip() in ["sim", "yes"]:
                    return opt

        # Questions where answer should be NO / NÃO
        # - Require visa sponsorship now or in the future
        negative_cues = ["sponsorship", "patrocínio", "visto", "visa"]
        if any(cue in q for cue in negative_cues):
            for opt in options:
                if opt.lower().strip() in ["não", "nao", "no"]:
                    return opt

        # Default fallback: prefer "Sim" / "Yes" if available
        for opt in options:
            if opt.lower().strip() in ["sim", "yes"]:
                return opt

        return options[0] if options else None

    def resolve_dropdown_option(self, label_text: str, available_options: List[str]) -> Optional[str]:
        t = label_text.lower()

        # Language proficiency (English, etc.)
        if any(k in t for k in ["english", "inglês", "idioma", "language", "proficiency"]):
            target_keywords = ["fluent", "fluente", "professional", "avançado", "advanced", "native", "nativo"]
            for target in target_keywords:
                for opt in available_options:
                    if target in opt.lower():
                        return opt

        # Country code / Código do país (check by content first - language-independent!)
        for opt in available_options:
            if "+55" in opt or "(55+)" in opt or "(+55)" in opt or "brasil" in opt.lower() or "brazil" in opt.lower() or "البرازيل" in opt:
                return opt

        # Education degree
        if any(k in t for k in ["degree", "escolaridade", "formação", "education", "graduação"]):
            target_keywords = ["bachelor", "bacharelado", "ensino superior", "superior completo", "master", "pós"]
            for target in target_keywords:
                for opt in available_options:
                    if target in opt.lower():
                        return opt

        # Email dropdown
        if "email" in t or "e-mail" in t:
            target_email = self.personal.get("email", "").lower()
            for opt in available_options:
                if target_email and target_email in opt.lower():
                    return opt

        # Notice period
        if any(k in t for k in ["notice", "aviso"]):
            target_keywords = ["immediate", "imediato", "15", "1 month", "1 mês", "2 weeks", "2 semanas"]
            for target in target_keywords:
                for opt in available_options:
                    if target in opt.lower():
                        return opt

        return None


class BrowserGymAutomationService:
    def __init__(self, headless: bool = True, session_state_path: Optional[str] = None):
        self.headless = headless
        self.session_state_path = session_state_path or DEFAULT_SESSION_FILE
        self.screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.session_state_path), exist_ok=True)

    async def _safe_screenshot(self, page: Page, path: str, timeout_ms: int = 4000) -> Optional[str]:
        """
        Takes a non-blocking screenshot, preventing timeouts caused by hanging web fonts.
        """
        try:
            await page.screenshot(path=path, timeout=timeout_ms, animations="disabled", full_page=False)
            logger.info(f"Audit screenshot capturado: {os.path.basename(path)}")
            return path
        except Exception as e:
            logger.debug(f"Screenshot bypass (demora de fontes do LinkedIn, não bloqueante): {e}")
            return None

    async def save_session_interactive(self, login_url: str = "https://www.linkedin.com/login") -> bool:
        """
        Opens a visible browser for the user to log in manually.
        Detects successful login and stores the persistent session state (cookies, tokens).
        """
        logger.info("Opening interactive browser for LinkedIn authentication...")
        print("\n" + "=" * 65)
        print(" [AÇÃO NECESSÁRIA] O navegador foi aberto para seu login.")
        print(" 1. Faça login na sua conta do LinkedIn.")
        print(" 2. Resolva qualquer verificação de 2 fatores ou Captcha se solicitado.")
        print(" 3. Assim que o feed do LinkedIn carregar, a sessão será salva automaticamente!")
        print("=" * 65 + "\n")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--start-maximized"]
            )
            context = await browser.new_context(
                viewport=None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(login_url, wait_until="domcontentloaded")

                # Wait up to 180 seconds for user to log in and land on the feed or jobs page
                for _ in range(90):
                    await asyncio.sleep(2)
                    current_url = page.url
                    if "/feed" in current_url or "/jobs" in current_url or "/mynetwork" in current_url:
                        logger.info("Login detected successfully! Capturing session state...")
                        await asyncio.sleep(3)
                        await context.storage_state(path=self.session_state_path)
                        logger.info(f"Session saved safely to: {self.session_state_path}")

                        # Sync with Supabase (if configured)
                        try:
                            from supabase_client import SupabaseService
                            supa = SupabaseService()
                            if supa.is_connected:
                                user_rec = supa.sync_applicant_profile(load_applicant_profile())
                                u_id = user_rec.get("id") if user_rec else None
                                with open(self.session_state_path, "r", encoding="utf-8") as sf:
                                    raw_session = sf.read()
                                supa.save_browser_session(user_id=u_id, session_data=raw_session, user_agent="Playwright-Chromium")
                                print("[SUPABASE] Sessão e perfil do candidato sincronizados com o banco de dados na nuvem!")
                            else:
                                print("[INFO] Operando em modo Self-Hosted local. A sessão está salva e pronta no arquivo local.")
                        except Exception as sync_err:
                            logger.debug(f"Supabase sync optional step: {sync_err}")

                        print(f"\n[SUCESSO] Sessão salva com sucesso em: {self.session_state_path}\n")
                        await browser.close()
                        return True

                logger.warning("Tempo limite de login excedido (180 segundos).")
            except Exception as e:
                logger.error(f"Erro durante o login interativo: {e}")
            finally:
                await browser.close()

        return False

    async def get_active_modal(self, page: Page):
        """
        Locates the active Easy Apply modal dialog in the DOM.
        Handles native <dialog> (with or without data-testid), role='dialog', and artdeco modal classes.
        """
        selectors = [
            "dialog[open]",
            "dialog[data-testid='dialog']",
            "dialog",
            "[role='dialog']",
            "div.jobs-easy-apply-modal",
            "div[data-test-modal]",
            ".artdeco-modal"
        ]
        for sel in selectors:
            try:
                modal = await page.query_selector(sel)
                if modal and await modal.is_visible():
                    return modal
            except Exception:
                continue
        return None

    async def fill_current_modal_step(self, page: Page, qa_engine: FormQAEngine, pdf_resume_path: Optional[str] = None):
        """
        Inspects the active Easy Apply modal and fills in inputs, selects, radios, and file uploads.
        Scoping is strictly confined to the active modal to prevent interference with background elements.
        """
        logger.info("Scanning and filling fields on the current modal step...")

        modal = await self.get_active_modal(page)
        root = modal if modal else page

        # 1. Handle File Upload (Resume PDF)
        if pdf_resume_path and os.path.exists(pdf_resume_path):
            file_inputs = await root.query_selector_all("input[type='file']")
            for f_inp in file_inputs:
                try:
                    await f_inp.set_input_files(pdf_resume_path)
                    logger.info(f"Attached resume PDF: {pdf_resume_path}")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.debug(f"File input: {e}")

        # 2. Handle Text, Tel, Number Inputs
        text_inputs = await root.query_selector_all(
            "input[type='text'], input[type='number'], input[type='tel'], input:not([type]), textarea"
        )
        for inp in text_inputs:
            try:
                # Check if input already has a value
                current_val = await inp.input_value()
                is_invalid = await inp.evaluate("el => el.getAttribute('aria-invalid') === 'true' || el.classList.contains('artdeco-text-input--error')")
                if not is_invalid and current_val and current_val.strip():
                    continue

                inp_id = await inp.get_attribute("id") or ""
                inp_name = await inp.get_attribute("name") or ""
                inp_type = await inp.get_attribute("type") or "text"

                # Find associated label
                label_text = ""
                if inp_id:
                    label_el = await root.query_selector(f"label[for='{inp_id}']")
                    if label_el:
                        label_text = await label_el.inner_text()

                if not label_text:
                    aria_label = await inp.get_attribute("aria-label") or ""
                    placeholder = await inp.get_attribute("placeholder") or ""
                    label_text = aria_label or placeholder

                if not label_text:
                    label_text = await inp.evaluate("el => el.closest('div')?.querySelector('label')?.innerText || ''")

                if not label_text and (inp_type == "tel" or any(p in (inp_id + inp_name).lower() for p in ["phone", "tel", "celular", "mobile", "movil"])):
                    label_text = "celular"

                answer = qa_engine.resolve_text_value(label_text, input_type=inp_type)

                # Resilient fallback for phone fields by attribute inspection
                if not answer and (inp_type == "tel" or any(p in (inp_id + inp_name).lower() for p in ["phone", "tel", "celular", "mobile", "movil"])):
                    answer = qa_engine.resolve_text_value("phone", input_type="tel")

                if answer is not None:
                    await inp.scroll_into_view_if_needed()
                    await inp.fill(str(answer))
                    await inp.evaluate("el => { el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }")
                    logger.info(f"Filled text field '{(label_text or inp_name).strip()[:30]}' with: {answer}")
                    await asyncio.sleep(0.3)
            except Exception as e:
                logger.debug(f"Could not fill input: {e}")

        # 3. Handle Select Dropdowns
        selects = await root.query_selector_all("select")
        for sel in selects:
            try:
                if not await sel.is_visible():
                    continue

                sel_id = await sel.get_attribute("id") or ""
                label_text = ""
                if sel_id:
                    label_el = await root.query_selector(f"label[for='{sel_id}']")
                    if label_el:
                        label_text = await label_el.inner_text()

                if not label_text:
                    label_text = await sel.evaluate("el => el.closest('div')?.querySelector('label')?.innerText || ''")

                options = await sel.query_selector_all("option")
                opt_texts = [await opt.inner_text() for opt in options]

                selected_opt = qa_engine.resolve_dropdown_option(label_text, opt_texts)
                if selected_opt:
                    await sel.select_option(label=selected_opt)
                    logger.info(f"Selected dropdown '{label_text.strip()[:30]}' with: {selected_opt}")
                    await asyncio.sleep(0.3)
            except Exception as e:
                logger.debug(f"Could not interact with select: {e}")

        # 4. Handle Radio Buttons (Fieldset-based & Standalone)
        handled_radio_names = set()

        # 4a. Process fieldsets (standard LinkedIn Form Builder pattern)
        fieldsets = await root.query_selector_all("fieldset")
        for fs in fieldsets:
            try:
                radios = await fs.query_selector_all("input[type='radio']")
                if not radios:
                    continue

                # Get question text
                legend = await fs.query_selector("legend, span.fb-form-element-label__title, label")
                q_text = (await legend.inner_text()).strip() if legend else ""

                # Check if already answered
                already_answered = any([await r.is_checked() for r in radios])
                if already_answered:
                    for r in radios:
                        n = await r.get_attribute("name")
                        if n:
                            handled_radio_names.add(n)
                    continue

                # Gather option info (radio input, label element, option text)
                opt_items = []
                for r in radios:
                    r_id = await r.get_attribute("id") or ""
                    r_name = await r.get_attribute("name") or ""
                    if r_name:
                        handled_radio_names.add(r_name)
                    r_val = await r.get_attribute("value") or ""

                    lbl_el = await fs.query_selector(f"label[for='{r_id}']") if r_id else None
                    if not lbl_el:
                        lbl_handle = await r.evaluate_handle("el => el.closest('label') || el.parentElement.querySelector('label')")
                        lbl_el = lbl_handle.as_element()

                    lbl_txt = (await lbl_el.inner_text()).strip() if lbl_el else r_val
                    opt_items.append((r, lbl_el, lbl_txt, r_val))

                option_labels = [item[2] for item in opt_items]
                chosen_label = qa_engine.resolve_radio_selection(q_text, option_labels)
                logger.info(f"Pergunta: '{q_text}' -> Opções: {option_labels} -> Escolhido: '{chosen_label}'")

                chosen_target = None
                for r, lbl, txt, val in opt_items:
                    if chosen_label and (chosen_label.lower() in txt.lower() or chosen_label.lower() in val.lower()):
                        chosen_target = (r, lbl)
                        break

                if not chosen_target and opt_items:
                    # Fallback to Sim / Yes
                    for r, lbl, txt, val in opt_items:
                        if any(y in txt.lower() or y in val.lower() for y in ["sim", "yes", "true"]):
                            chosen_target = (r, lbl)
                            break
                    if not chosen_target:
                        chosen_target = (opt_items[0][0], opt_items[0][1])

                if chosen_target:
                    c_radio, c_label = chosen_target
                    if c_label:
                        await c_label.scroll_into_view_if_needed()
                        await c_label.click(force=True)
                    else:
                        await c_radio.scroll_into_view_if_needed()
                        await c_radio.click(force=True)

                    # Ensure state is updated in DOM & React/Ember bindings
                    await c_radio.evaluate("""el => {
                        el.checked = true;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }""")
                    logger.info(f"Opção de rádio marcada com sucesso: '{q_text}'")
                    await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"Erro ao processar grupo de rádio (fieldset): {e}")

        # 4b. Standalone radio buttons not inside fieldsets
        all_radios = await root.query_selector_all("input[type='radio']")
        for r in all_radios:
            try:
                r_name = await r.get_attribute("name") or ""
                if r_name in handled_radio_names:
                    continue
                if await r.is_checked():
                    continue

                r_id = await r.get_attribute("id") or ""
                lbl_el = await root.query_selector(f"label[for='{r_id}']") if r_id else None
                lbl_txt = (await lbl_el.inner_text()).lower() if lbl_el else ""
                val = (await r.get_attribute("value") or "").lower()

                # Prefer "Sim"
                if any(y in lbl_txt or y in val for y in ["sim", "yes", "true"]):
                    if lbl_el:
                        await lbl_el.click(force=True)
                    else:
                        await r.click(force=True)
                    await r.evaluate("el => { el.checked = true; el.dispatchEvent(new Event('change', {bubbles: true})); }")
                    logger.info(f"Opção de rádio avulsa selecionada: {lbl_txt or val}")
                    if r_name:
                        handled_radio_names.add(r_name)
            except Exception as e:
                logger.debug(f"Erro em rádio avulso: {e}")

        # 5. Handle Mandatory Checkboxes (Consent / Terms)
        checkboxes = await root.query_selector_all("input[type='checkbox']")
        for cb in checkboxes:
            try:
                cb_id = await cb.get_attribute("id") or ""
                lbl = await root.query_selector(f"label[for='{cb_id}']") if cb_id else None
                lbl_text = (await lbl.inner_text()).lower() if lbl else ""
                if any(w in lbl_text for w in ["concordo", "aceito", "termos", "consent", "agree", "policy"]):
                    if not await cb.is_checked():
                        if lbl:
                            await lbl.click(force=True)
                        else:
                            await cb.click(force=True)
                        await cb.evaluate("el => { el.checked = true; el.dispatchEvent(new Event('change', {bubbles: true})); }")
                        logger.info(f"Checkbox de consentimento marcado: '{lbl_text[:30]}'")
            except Exception as e:
                logger.debug(f"Checkbox interaction error: {e}")

    async def extract_job_details(self, page: Page) -> Dict[str, str]:
        """
        Extracts the job title, company name, and full description text directly from the LinkedIn DOM.
        Uses intelligent waiting, scrolling, and multi-selector fallback.
        """
        try:
            # Wait up to 6 seconds for main job containers to render
            for sel in ["#job-details", ".jobs-description__content", "h1", ".jobs-unified-top-card"]:
                try:
                    await page.wait_for_selector(sel, timeout=3000)
                    break
                except Exception:
                    pass

            # Scroll slightly to trigger dynamic lazy loading of the job description
            try:
                await page.evaluate("window.scrollBy(0, 350)")
                await asyncio.sleep(1)
            except Exception:
                pass

            # If there is a 'Ver mais' / 'Show more' button, click it to get full description
            try:
                more_btn = await page.query_selector(
                    "button[aria-label*='mais'], button:has-text('Exibir mais'), button:has-text('Ver mais'), button:has-text('Show more')"
                )
                if more_btn and await more_btn.is_visible():
                    await more_btn.click(force=True)
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            # 1. Job Title
            title = ""
            for t_sel in [
                "h1.job-details-jobs-unified-top-card__job-title",
                "h1.jobs-unified-top-card__job-title",
                "h1.t-24",
                "h2.job-details-jobs-unified-top-card__job-title",
                ".job-details-jobs-unified-top-card h1",
                ".jobs-unified-top-card h1",
                "h1"
            ]:
                el = await page.query_selector(t_sel)
                if el and await el.is_visible():
                    txt = (await el.inner_text()).strip()
                    if txt and "linkedin" not in txt.lower():
                        title = txt
                        break

            if not title or title.lower() in ["vaga", "linkedin"]:
                pg_title = await page.title()
                if pg_title and "linkedin" in pg_title.lower():
                    clean = pg_title.split("|")[0].strip()
                    if " na " in clean:
                        title = clean.split(" na ", 1)[0].strip()
                    elif " no " in clean:
                        title = clean.split(" no ", 1)[0].strip()
                    elif "-" in clean:
                        title = clean.split("-")[0].strip()
                    else:
                        title = clean
                else:
                    title = pg_title or "Vaga LinkedIn"

            # 2. Company Name
            company = ""
            for c_sel in [
                "a[href*='/company/']",
                "a.job-details-jobs-unified-top-card__company-name",
                ".jobs-unified-top-card__company-name a",
                ".jobs-unified-top-card__company-name",
                ".job-details-jobs-unified-top-card__primary-description a",
                "a[data-tracking-control-name*='company_name']",
                ".jobs-unified-top-card__subtitle-primary-grouping a"
            ]:
                el = await page.query_selector(c_sel)
                if el:
                    txt = (await el.inner_text()).strip()
                    if txt and len(txt) > 1 and "linkedin" not in txt.lower():
                        company = txt
                        break

            if not company:
                pg_title = await page.title()
                clean = pg_title.split("|")[0].strip()
                if " na " in clean:
                    company = clean.split(" na ", 1)[1].strip()
                elif " no " in clean:
                    company = clean.split(" no ", 1)[1].strip()
                elif " at " in clean:
                    company = clean.split(" at ", 1)[1].strip()
                elif "-" in clean:
                    parts = clean.split("-")
                    if len(parts) > 1:
                        company = parts[1].strip()

            if not company:
                company = "Empresa Contratante"

            # 3. Full Job Description
            description = ""
            for d_sel in [
                "#job-details",
                "div.jobs-description-content__text",
                "div.jobs-description__content",
                "div.jobs-box__html-content",
                "article.jobs-description__container",
                "div[class*='jobs-description']",
                "div[class*='description__text']",
                "article"
            ]:
                el = await page.query_selector(d_sel)
                if el:
                    txt = (await el.inner_text()).strip()
                    if len(txt) > len(description):
                        description = txt

            if not description:
                try:
                    description = await page.evaluate("""() => {
                        const candidates = document.querySelectorAll('#job-details, div[class*="jobs-description"], article, div[class*="description"]');
                        let longest = '';
                        for (const c of candidates) {
                            const t = (c.innerText || '').trim();
                            if (t.length > longest.length) longest = t;
                        }
                        return longest;
                    }""")
                except Exception:
                    pass

            return {
                "title": title or "Vaga LinkedIn",
                "company": company or "Empresa",
                "description": description
            }
        except Exception as e:
            logger.warning(f"Falha ao extrair detalhes da página da vaga: {e}")
            return {"title": "Vaga LinkedIn", "company": "Empresa", "description": ""}

    async def execute_job_application(
        self,
        job_url: str,
        applicant_data: Dict[str, Any],
        pdf_resume_path: Optional[str] = None,
        session_cookies: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Executes LinkedIn Easy Apply automation using persistent storage state and Form QA Engine.
        """
        logger.info(f"Initiating auto-apply workflow for: {job_url}")
        qa_engine = FormQAEngine(applicant_data)

        result = {
            "status": "pending",
            "job_url": job_url,
            "resume_pdf": pdf_resume_path,
            "screenshot_path": None,
            "error_reason": None,
            "steps_completed": 0,
            "job_details": None
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

            # Load persistent storage state if available
            context_kwargs = {
                "viewport": {"width": 1280, "height": 720},
                "locale": "pt-BR",
                "extra_http_headers": {
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
                },
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            }
            if os.path.exists(self.session_state_path):
                logger.info(f"Loading persistent session state from: {self.session_state_path}")
                context_kwargs["storage_state"] = self.session_state_path

            context = await browser.new_context(**context_kwargs)

            # Ensure language cookie is always pt-BR
            await context.add_cookies([
                {"name": "lang", "value": "v=2&lang=pt-br", "domain": ".linkedin.com", "path": "/"}
            ])

            if session_cookies:
                await context.add_cookies(session_cookies)

            page = await context.new_page()

            try:
                # 1. Normalize and Navigate to target Job URL
                target_url = normalize_job_url(job_url)
                logger.info(f"Navigating to job page: {target_url}")
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Extract and read job details directly from the DOM!
                job_info = await self.extract_job_details(page)
                result["job_details"] = job_info
                logger.info(f"--- VAGA LIDA: '{job_info['title']}' na empresa '{job_info['company']}' ---")
                logger.info(f"Texto da vaga capturado: {len(job_info['description'])} caracteres para análise ATS.")

                # Sync job posting to Supabase if connected
                try:
                    from supabase_client import SupabaseService
                    supa = SupabaseService()
                    if supa.is_connected and job_info.get("description"):
                        ext_id = target_url.rstrip("/").split("/")[-1]
                        supa.insert_job_posting({
                            "platform": "linkedin",
                            "external_job_id": ext_id,
                            "title": job_info["title"],
                            "company": job_info["company"],
                            "location": "Brasil",
                            "description_raw": job_info["description"],
                            "apply_url": target_url,
                            "is_easy_apply": True
                        })
                        logger.info(f"Vaga '{job_info['title']}' persistida na tabela 'job_postings' do Supabase!")
                except Exception as e:
                    logger.debug(f"Optional Supabase job posting sync: {e}")

                # Capture entry screenshot safely (non-blocking)
                timestamp = int(asyncio.get_event_loop().time())
                screenshot_filename = f"job_apply_{timestamp}.png"
                screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
                shot = await self._safe_screenshot(page, screenshot_path)
                result["screenshot_path"] = shot

                # 2. Check for Easy Apply / Candidatura Simplificada button with retry
                apply_selectors = (
                    "button:has-text('Candidatura simplificada'), "
                    "button:has-text('Candidatura fácil'), "
                    "button:has-text('Easy Apply'), "
                    "button.jobs-apply-button, "
                    ".jobs-apply-button--top-card button, "
                    "button[aria-label*='Candidatura simplificada'], "
                    "button[aria-label*='Candidatura'], "
                    "button[aria-label*='simplificada']"
                )
                apply_button = None
                for _ in range(6):
                    apply_button = await page.query_selector(apply_selectors)
                    if apply_button and await apply_button.is_visible():
                        break
                    await asyncio.sleep(1)

                if not apply_button:
                    logger.warning("No 'Easy Apply' / 'Candidatura simplificada' button found on page.")
                    result["status"] = "requires_manual"
                    result["error_reason"] = "Botão 'Candidatura simplificada' não encontrado (vaga externa ou já candidatado)."
                    await browser.close()
                    return result

                logger.info("Found apply button! Clicking 'Candidatura simplificada'...")
                await apply_button.scroll_into_view_if_needed()
                await apply_button.click()
                await asyncio.sleep(2)

                # 3. Multi-Step Form Navigation Loop
                max_steps = 10
                current_step = 0
                submitted = False

                while current_step < max_steps:
                    current_step += 1
                    result["steps_completed"] = current_step
                    logger.info(f"Processing application modal step {current_step}...")

                    # 1. Locate active modal dialog
                    modal = await self.get_active_modal(page)
                    if not modal:
                        logger.info("No active modal found. Checking for submission confirmation or dismissal...")
                        confirm_dismiss = await page.query_selector(
                            "button:has-text('Concluído'), button:has-text('Done'), button[aria-label*='Fechar'], button[aria-label*='Dismiss']"
                        )
                        if confirm_dismiss and await confirm_dismiss.is_visible():
                            await confirm_dismiss.click(force=True)
                            submitted = True
                            result["status"] = "SUBMITTED"
                            break
                        break

                    # 2. Fill fields in the current screen
                    await self.fill_current_modal_step(page, qa_engine, pdf_resume_path)
                    await asyncio.sleep(1)

                    # 3. Locate primary action button STRICTLY INSIDE THE MODAL
                    action_button_selectors = [
                        "button:has-text('Enviar candidatura')",
                        "button:has-text('Submit application')",
                        "button:has-text('Enviar inscrição')",
                        "button:has-text('Avaliar')",
                        "button:has-text('Revisar')",
                        "button:has-text('Examinar')",
                        "button:has-text('Avançar')",
                        "button:has-text('Review')",
                        "button:has-text('Next')",
                        "button:has-text('التالي')",
                        "button[data-easy-apply-next-button]",
                        "footer button.artdeco-button--primary",
                        ".artdeco-modal__actionbar button.artdeco-button--primary",
                        "button.artdeco-button--primary"
                    ]

                    primary_button = None
                    for sel in action_button_selectors:
                        btn = await modal.query_selector(sel)
                        if btn and await btn.is_visible():
                            primary_button = btn
                            break

                    if primary_button:
                        btn_text = (await primary_button.inner_text()).strip().lower()
                        logger.info(f"Modal primary action button detected: '{btn_text}'")

                        # If disabled, re-check form fields
                        is_disabled = await primary_button.evaluate("b => b.disabled || b.getAttribute('aria-disabled') === 'true'")
                        if is_disabled:
                            logger.warning(f"Botão '{btn_text}' está desabilitado. Reavaliando campos do modal...")
                            await self.fill_current_modal_step(page, qa_engine, pdf_resume_path)
                            await asyncio.sleep(1)

                        if any(k in btn_text for k in ['enviar', 'submit', 'inscrição', 'إرسال', 'confirmar']):
                            logger.info("Found final Submit button! Taking audit screenshot and submitting...")
                            await self._safe_screenshot(page, screenshot_path)
                            await primary_button.scroll_into_view_if_needed()
                            await primary_button.click(force=True)
                            await asyncio.sleep(3)
                            submitted = True
                            result["status"] = "SUBMITTED"
                            logger.info("Application submitted successfully!")

                            # Check for confirmation close button
                            try:
                                close_btn = await page.query_selector("button:has-text('Concluído'), button:has-text('Done'), button[aria-label*='Fechar']")
                                if close_btn and await close_btn.is_visible():
                                    await close_btn.click(force=True)
                            except Exception:
                                pass
                            break
                        else:
                            logger.info(f"Advancing modal step with button: '{btn_text}'...")
                            await primary_button.scroll_into_view_if_needed()
                            await primary_button.click(force=True)
                            await asyncio.sleep(2)
                            continue

                    logger.warning("No next/submit button detected inside modal. Form may require manual review.")
                    break

                if not submitted and result["status"] == "pending":
                    result["status"] = "requires_manual"
                    result["error_reason"] = "Formulário continha etapas ou validações não automáticas."

                # Final state audit screenshot
                await self._safe_screenshot(page, screenshot_path)

            except Exception as e:
                logger.error(f"Error during job application execution: {e}")
                result["status"] = "failed"
                result["error_reason"] = str(e)
            finally:
                await browser.close()

        return result


def load_applicant_profile(profile_path: Optional[str] = None) -> Dict[str, Any]:
    target = profile_path or DEFAULT_PROFILE_FILE
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read applicant profile at {target}: {e}")
    return {}


async def main():
    """
    CLI runner for BrowserGymAutomationService.
    Supports --login (interactive session save) and --apply (auto application).
    """
    import argparse
    parser = argparse.ArgumentParser(description="BrowserGym LinkedIn Automation Runner")
    parser.add_argument("--login", action="store_true", help="Launch interactive browser to log in and save session")
    parser.add_argument("--apply", action="store_true", help="Execute job application flow")
    parser.add_argument("--job-url", type=str, default="https://www.linkedin.com/jobs/search/?keywords=Developer", help="Target LinkedIn job posting URL")
    parser.add_argument("--resume-pdf", type=str, default=None, help="Path to ATS Resume PDF file")
    parser.add_argument("--session-state", type=str, default=DEFAULT_SESSION_FILE, help="Path to persistent session state JSON")
    parser.add_argument("--profile-file", type=str, default=DEFAULT_PROFILE_FILE, help="Path to applicant profile JSON")
    parser.add_argument("--headless", type=str, default="true", help="Run browser in headless mode (true/false)")

    args = parser.parse_args()
    headless_bool = args.headless.lower() in ["true", "1", "yes"]

    service = BrowserGymAutomationService(headless=headless_bool, session_state_path=args.session_state)

    if args.login:
        success = await service.save_session_interactive()
        sys.exit(0 if success else 1)

    profile_data = load_applicant_profile(args.profile_file)

    logger.info("Executing Job Application workflow...")
    res = await service.execute_job_application(
        job_url=args.job_url,
        applicant_data=profile_data,
        pdf_resume_path=args.resume_pdf
    )
    print("\n--- Execution Result ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
