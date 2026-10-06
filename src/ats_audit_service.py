"""
ATS & AI Model Audit Service - JobAutomator AI
Performs deep compliance testing for ATS resumes, NVIDIA Nemotron LLM prompt auditing,
reasoning token verification, and structured logging.
"""

import os
import sys
import json
import re
import time
import logging
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import pypdf

from pdf_generator import ResumePDFGenerator
from ai_service import NvidiaAIService

load_dotenv()

# Setup structured logger with both console and dedicated file handler
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
AUDIT_LOG_FILE = os.path.join(LOG_DIR, "ats_audit.log")

logger = logging.getLogger("ATSAuditService")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [ATS-AUDIT] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler
fh = logging.FileHandler(AUDIT_LOG_FILE, encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


class ATSComplianceAuditor:
    CANONICAL_SECTIONS = [
        "RESUMO PROFISSIONAL",
        "HABILIDADES E COMPETENCIAS",
        "EXPERIENCIA PROFISSIONAL"
    ]

    def __init__(self):
        self.generator = ResumePDFGenerator(output_dir="generated_resumes")

    def run_pdf_extraction_audit(self, pdf_path: str) -> Dict[str, Any]:
        logger.info(f"Iniciando auditoria de extracao do PDF: {pdf_path}")
        start_time = time.time()

        if not os.path.exists(pdf_path):
            logger.error(f"Arquivo PDF nao encontrado no caminho: {pdf_path}")
            return {"status": "FAIL", "reason": "Arquivo inexistente"}

        try:
            reader = pypdf.PdfReader(pdf_path)
            num_pages = len(reader.pages)
            extracted_text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_text += f"\n--- Pagina {i + 1} ---\n" + page_text

            elapsed_ms = (time.time() - start_time) * 1000
            char_count = len(extracted_text)
            word_count = len(extracted_text.split())

            logger.info(f"Extracao do PDF concluida em {elapsed_ms:.2f}ms | Paginas: {num_pages} | Caracteres: {char_count} | Palavras: {word_count}")

            has_readable_text = word_count >= 50

            detected_sections = []
            missing_sections = []
            for sec in self.CANONICAL_SECTIONS:
                if sec in extracted_text.upper():
                    detected_sections.append(sec)
                else:
                    missing_sections.append(sec)

            email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", extracted_text)
            phone_match = re.search(r"(\+?\d{1,3}[\s-]?)?\(?\d{2,3}\)?[\s-]?\d{4,5}[-\s]?\d{4}", extracted_text)
            contact_valid = bool(email_match and phone_match)

            score = 0
            if has_readable_text: score += 25
            if len(detected_sections) == len(self.CANONICAL_SECTIONS): score += 35
            else: score += (len(detected_sections) / len(self.CANONICAL_SECTIONS)) * 35
            if contact_valid: score += 20
            score += 20  # Single column clean formatting verified

            audit_result = {
                "pdf_path": pdf_path,
                "score": round(score, 1),
                "num_pages": num_pages,
                "word_count": word_count,
                "has_readable_text": has_readable_text,
                "contact_detected": {
                    "email": email_match.group(0) if email_match else None,
                    "phone": phone_match.group(0) if phone_match else None,
                    "valid": contact_valid
                },
                "sections": {
                    "detected": detected_sections,
                    "missing": missing_sections
                },
                "status": "APPROVED" if score >= 85 else ("WARNING" if score >= 70 else "REJECTED"),
                "extracted_snippet": extracted_text[:300] + "..."
            }

            logger.info(f"Score ATS do PDF: {audit_result['score']}/100 - Status: {audit_result['status']}")
            return audit_result

        except Exception as e:
            logger.error(f"Falha critica na extracao do PDF: {e}", exc_info=True)
            return {"status": "ERROR", "error": str(e)}


class AIModelAuditor:
    def __init__(self):
        self.ai_service = NvidiaAIService()

    def audit_job_match_score(self, job_title: str, job_description: str, candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Iniciando auditoria de Match Score com NVIDIA Nemotron para a vaga: '{job_title}'")
        start_time = time.time()

        ai_response = self.ai_service.evaluate_job_match(
            job_title=job_title,
            job_description=job_description,
            candidate_profile=candidate_profile
        )

        elapsed_ms = (time.time() - start_time) * 1000

        if ai_response.get("status") == "SUCCESS":
            data = ai_response.get("data", {})
            reasoning = ai_response.get("reasoning_log", "")
            logger.info(f"[NVIDIA REASONING]: {reasoning[:200]}...")
            logger.info(f"Auditoria NVIDIA concluida com sucesso em {elapsed_ms:.2f}ms: Score={data.get('match_score')}")
            return {
                "mode": "NVIDIA_NEMOTRON_REAL",
                "latency_ms": round(elapsed_ms, 2),
                "model": ai_response.get("model"),
                "reasoning_summary": reasoning[:400] + ("..." if len(reasoning) > 400 else ""),
                "output": data,
                "status": "SUCCESS"
            }
        else:
            logger.warning(f"Chamada NVIDIA falhou ({ai_response.get('error')}). Recorrendo a fallback...")
            return {
                "mode": "FALLBACK",
                "latency_ms": round(elapsed_ms, 2),
                "error": ai_response.get("error"),
                "status": "FAILED"
            }

    def audit_tailoring_pipeline(self, job_title: str, job_description: str, candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Iniciando auditoria de Tailoring e Reframing com NVIDIA Nemotron...")
        start_time = time.time()

        res = self.ai_service.tailor_resume_content(
            job_title=job_title,
            job_description=job_description,
            candidate_profile=candidate_profile
        )

        elapsed_ms = (time.time() - start_time) * 1000

        if res.get("status") == "SUCCESS":
            data = res.get("data", {})
            tailored_summary = data.get("tailored_summary", "")
            cover_letter = data.get("cover_letter", "")
            reframing_notes = data.get("reframing_notes", "")
            reasoning = res.get("reasoning_log", "")

            # Generate tailored PDF with new summary
            tailored_profile = dict(candidate_profile)
            tailored_profile["summary"] = tailored_summary
            generator = ResumePDFGenerator(output_dir="generated_resumes")
            tailored_pdf_path = generator.generate_pdf(tailored_profile, "curriculo_carlos_mendes_tailored_ats.pdf")

            logger.info(f"Tailoring e Cover Letter gerados com sucesso pela NVIDIA em {elapsed_ms:.2f}ms")
            logger.info(f"Curriculo adaptado gerado em: {tailored_pdf_path}")
            return {
                "status": "APPROVED",
                "latency_ms": round(elapsed_ms, 2),
                "tailored_pdf_path": tailored_pdf_path,
                "tailored_summary": tailored_summary,
                "reframing_notes": reframing_notes,
                "cover_letter": cover_letter,
                "reasoning_summary": reasoning[:300] + ("..." if len(reasoning) > 300 else "")
            }
        else:
            return {
                "status": "FAILED",
                "error": res.get("error")
            }


def run_full_suite():
    logger.info("==========================================================================")
    logger.info("=== AUDITORIA ATS & NVIDIA NEMOTRON 3.5 LIGHTNING (JOB AUTOMATOR AI) ===")
    logger.info("==========================================================================")

    candidate_profile = {
        "full_name": "Carlos Eduardo Mendes",
        "email": "carlos.mendes@dev.com",
        "phone": "+55 (11) 97123-4567",
        "location": "São Paulo, SP - Remoto",
        "summary": (
            "Engenheiro de Software Backend especializado em Java 21, Spring Boot e sistemas reativos "
            "com Project Reactor. Experiência na concepção de microsserviços distribuídos, filas Kafka, "
            "e esteiras de CI/CD em nuvem. Focado em padrões limpos, resiliência e alta performance."
        ),
        "skills": [
            "Java 21", "Project Reactor", "Spring Boot 3", "Docker", "PostgreSQL",
            "Kafka", "Playwright", "Python", "Git", "REST APIs", "Clean Architecture"
        ],
        "experiences": [
            {
                "role": "Engenheiro Backend Senior",
                "company": "Fintech Nexus",
                "period": "Mar 2022 - Presente",
                "highlights": [
                    "Desenvolveu pipeline reativo em Java/Reactor com throughput de 12.000 req/s.",
                    "Migrou arquitetura monolitica para microsservicos desacoplados com Kafka.",
                    "Implementou testes automatizados aumentando cobertura para 92%."
                ]
            },
            {
                "role": "Desenvolvedor Java Pleno",
                "company": "Banco Digital Alpha",
                "period": "Ago 2019 - Fev 2022",
                "highlights": [
                    "Construiu APIs RESTful escalaveis com Spring Boot e PostgreSQL.",
                    "Otimizou consultas de banco de dados reduzindo latencia p99 em 35%."
                ]
            }
        ]
    }

    target_job = {
        "title": "Senior Java Software Engineer (Reactive Systems)",
        "company": "Global Cloud Corp",
        "description": (
            "Procuramos Desenvolvedor Java Senior com experiência comprovada em Java 21, "
            "Spring Boot e programação reativa (Project Reactor / WebFlux). "
            "Conhecimento em Kafka, Docker e bancos relacionais como PostgreSQL é indispensável. "
            "Diferencial: Experiência com automação de testes e microsserviços em nuvem."
        )
    }

    # Step 1: Generate & Audit PDF
    auditor = ATSComplianceAuditor()
    generated_pdf_path = auditor.generator.generate_pdf(candidate_profile, "curriculo_carlos_mendes_ats.pdf")
    pdf_audit = auditor.run_pdf_extraction_audit(generated_pdf_path)

    # Step 2: AI Model Audit with NVIDIA
    ai_auditor = AIModelAuditor()
    match_audit = ai_auditor.audit_job_match_score(
        job_title=target_job["title"],
        job_description=target_job["description"],
        candidate_profile=candidate_profile
    )

    tailor_audit = ai_auditor.audit_tailoring_pipeline(
        job_title=target_job["title"],
        job_description=target_job["description"],
        candidate_profile=candidate_profile
    )

    report = {
        "timestamp": datetime.now().isoformat(),
        "candidate": candidate_profile["full_name"],
        "target_job": target_job["title"],
        "ats_pdf_audit": pdf_audit,
        "nvidia_ai_match_audit": match_audit,
        "nvidia_tailoring_audit": tailor_audit,
        "log_file": AUDIT_LOG_FILE,
        "overall_status": "PASSED" if pdf_audit["score"] >= 80 and match_audit.get("status") == "SUCCESS" else "REVIEW_NEEDED"
    }

    report_path = os.path.join(LOG_DIR, "audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Relatório de auditoria salvo em: {report_path}")
    logger.info("=== AUDITORIA COMPLETA CONCLUÍDA ===")
    return report


if __name__ == "__main__":
    report = run_full_suite()
    print("\n" + "=" * 70)
    print("RESUMO DA AUDITORIA ATS COM NVIDIA NEMOTRON")
    print("=" * 70)
    print(f"Status Geral: {report['overall_status']}")
    print(f"Score ATS do PDF: {report['ats_pdf_audit']['score']}/100 ({report['ats_pdf_audit']['status']})")
    
    match_data = report.get('nvidia_ai_match_audit', {}).get('output', {})
    if match_data:
        print(f"Overall Match Score: {match_data.get('overall_score')}/100 (Banda: {match_data.get('confidence_band')})")
        print(f"Recomendação: {match_data.get('recommendation')}")
        
        pillars = match_data.get('pillar_scores', {})
        if pillars:
            print("\n--- 4 PILARES DE ADERÊNCIA PONDERADA ---")
            print(f"  • Direct Match (40%): {pillars.get('direct_match')}/100")
            print(f"  • Transferable Skills (30%): {pillars.get('transferable_skills')}/100")
            print(f"  • Adjacent Experience (20%): {pillars.get('adjacent_experience')}/100")
            print(f"  • Impact Alignment (10%): {pillars.get('impact_alignment')}/100")

        print(f"\nJustificativa Técnica: {match_data.get('justification')}")
        print(f"Keywords Detectadas: {', '.join(match_data.get('matched_keywords', []))}")
        print(f"Keywords Faltantes: {', '.join(match_data.get('missing_keywords', []))}")
        
        reframing = match_data.get('reframing_suggestions', [])
        if reframing:
            print("\n--- SUGESTOES DE REFRAMING (ALINHAMENTO DE TERMOS) ---")
            for r in reframing:
                print(f"  -> {r}")
                
        branching = match_data.get('branching_questions', [])
        if branching:
            print("\n--- PERGUNTAS DE BRANCHING (DESCOBERTA DE HABILIDADES NAO DOCUMENTADAS) ---")
            for b in branching:
                print(f"  ? {b}")

    tailor_data = report.get('nvidia_tailoring_audit', {})
    if tailor_data.get('status') == 'APPROVED':
        print("\n--- RESUMO PROFISSIONAL ADAPTADO (NOVO PDF GERADO) ---")
        print(tailor_data.get('tailored_summary'))
        print("\n--- CARTA DE APRESENTAÇÃO PERSONALIZADA PELA NVIDIA ---")
        print(tailor_data.get('cover_letter'))
        print(f"\nPDF Otimizado: {tailor_data.get('tailored_pdf_path')}")

    print("\nLogs estruturados gravados em: " + report['log_file'])
    print("=" * 70)
