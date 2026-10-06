"""
ATS Resume PDF Generator for JobAutomator AI.
Generates clean, single-column, ATS-friendly PDF resumes from structured candidate data.
"""

import os
import json
import logging
from typing import Dict, Any
from fpdf import FPDF
from fpdf.enums import XPos, YPos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PDFGenerator")


class ATSResumePDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


class ResumePDFGenerator:
    def __init__(self, output_dir: str = "generated_resumes"):
        self.output_dir = os.path.join(os.getcwd(), output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize(self, text: str) -> str:
        """Replaces unsupported unicode characters with ASCII equivalents for standard Helvetica."""
        if not text:
            return ""
        replacements = {
            "—": "-", "–": "-", "•": "-",
            "“": '"', "”": '"', "‘": "'", "’": "'",
            "ã": "a", "á": "a", "à": "a", "â": "a",
            "é": "e", "ê": "e", "í": "i",
            "ó": "o", "õ": "o", "ô": "o",
            "ú": "u", "ü": "u", "ç": "c",
            "Ã": "A", "Á": "A", "À": "A", "Â": "A",
            "É": "E", "Ê": "E", "Í": "I",
            "Ó": "O", "Õ": "O", "Ô": "O",
            "Ú": "U", "Ü": "U", "Ç": "C"
        }
        for orig, sub in replacements.items():
            text = text.replace(orig, sub)
        return text

    def generate_pdf(self, resume_data: Dict[str, Any], filename: str) -> str:
        pdf = ATSResumePDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(15, 15, 15)

        w = pdf.epw # Effective page width

        # 1. Header: Name & Contact Info
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(33, 37, 41)
        name = self._sanitize(resume_data.get("full_name", "Candidato"))
        pdf.cell(w, 10, name, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(100, 100, 100)
        contacts = []
        if resume_data.get("email"): contacts.append(f"Email: {resume_data.get('email')}")
        if resume_data.get("phone"): contacts.append(f"Tel: {resume_data.get('phone')}")
        if resume_data.get("location"): contacts.append(f"Local: {resume_data.get('location')}")
        if resume_data.get("linkedin"): contacts.append(f"LinkedIn: {resume_data.get('linkedin')}")
        if resume_data.get("portfolio"): contacts.append(f"Portfolio: {resume_data.get('portfolio')}")
        contact_info = " | ".join(contacts)
        pdf.cell(w, 6, self._sanitize(contact_info), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        pdf.ln(3)

        # Divider line
        pdf.set_draw_color(200, 200, 200)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

        # 2. Section: Professional Summary
        if "summary" in resume_data and resume_data["summary"]:
            self._add_section_title(pdf, "RESUMO PROFISSIONAL")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(w, 5, self._sanitize(resume_data["summary"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(4)

        # 3. Section: Skills / Competências (Suporta lista simples ou dicionário categorizado)
        if "skills" in resume_data and resume_data["skills"]:
            self._add_section_title(pdf, "HABILIDADES E COMPETENCIAS")
            skills_data = resume_data["skills"]
            if isinstance(skills_data, dict):
                for category, items in skills_data.items():
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.set_text_color(0, 51, 102)
                    pdf.cell(w, 4.5, self._sanitize(f"{category.upper()}:"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.set_font("Helvetica", "", 9.5)
                    pdf.set_text_color(40, 40, 40)
                    items_str = ", ".join(items) if isinstance(items, list) else str(items)
                    pdf.multi_cell(w, 4.5, self._sanitize(items_str), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.ln(1.5)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
                skills_str = ", ".join(skills_data) if isinstance(skills_data, list) else str(skills_data)
                pdf.multi_cell(w, 5, self._sanitize(skills_str), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)

        # 4. Section: Experience
        if "experiences" in resume_data and resume_data["experiences"]:
            self._add_section_title(pdf, "EXPERIENCIA PROFISSIONAL")
            for exp in resume_data["experiences"]:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 51, 102)
                header_exp = f"{exp.get('role', '')} - {exp.get('company', '')}"
                pdf.cell(w, 6, self._sanitize(header_exp), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(120, 120, 120)
                period = f"Periodo: {exp.get('period', '')}"
                pdf.cell(w, 5, self._sanitize(period), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
                if "highlights" in exp:
                    for item in exp["highlights"]:
                        pdf.multi_cell(w, 5, self._sanitize(f"- {item}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(3)

        # 5. Section: Education / Formação Acadêmica
        if "education" in resume_data and resume_data["education"]:
            self._add_section_title(pdf, "FORMACAO ACADEMICA")
            for edu in resume_data["education"]:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(0, 51, 102)
                course = f"{edu.get('degree', '')} - {edu.get('institution', '')}"
                pdf.cell(w, 5, self._sanitize(course), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(120, 120, 120)
                year_info = f"Periodo: {edu.get('period', '')}"
                if "details" in edu:
                    year_info += f" | {edu.get('details')}"
                pdf.cell(w, 5, self._sanitize(year_info), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(2)
            pdf.ln(2)

        # 6. Section: Certifications & Titles / Certificações e Títulos
        if "certifications" in resume_data and resume_data["certifications"]:
            self._add_section_title(pdf, "CERTIFICACOES E TITULOS")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            for cert in resume_data["certifications"]:
                pdf.multi_cell(w, 5, self._sanitize(f"- {cert}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)

        # 7. Section: Publications & Research / Publicações e Pesquisas
        if "publications" in resume_data and resume_data["publications"]:
            self._add_section_title(pdf, "PUBLICACOES E PESQUISAS")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            for pub in resume_data["publications"]:
                pdf.multi_cell(w, 5, self._sanitize(f"- {pub}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)

        # 8. Section: Languages / Idiomas
        if "languages" in resume_data and resume_data["languages"]:
            self._add_section_title(pdf, "IDIOMAS")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            lang_items = []
            for lang in resume_data["languages"]:
                if isinstance(lang, dict):
                    lang_items.append(f"{lang.get('language', '')} ({lang.get('proficiency', '')})")
                else:
                    lang_items.append(str(lang))
            pdf.multi_cell(w, 5, self._sanitize(" | ".join(lang_items)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)

        # Output path
        output_path = os.path.join(self.output_dir, filename)
        pdf.output(output_path)
        logger.info(f"Resume PDF successfully generated at: {output_path}")
        return output_path

    def _add_section_title(self, pdf: FPDF, title: str):
        w = pdf.epw
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(w, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(0, 51, 102)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)


def main():
    logger.info("Running ResumePDFGenerator test...")
    generator = ResumePDFGenerator()

    sample_resume = {
        "full_name": "João Silva",
        "email": "joao.silva@email.com",
        "phone": "+55 (11) 98765-4321",
        "location": "São Paulo, SP - Brasil",
        "summary": "Desenvolvedor Java Senior especializado em sistemas reativos de alta concorrencia com Spring Boot e Project Reactor. Experiencia em arquitetura de multi-agentes e automacao web.",
        "skills": ["Java 21", "Project Reactor", "Spring Boot", "BrowserGym", "Python", "PostgreSQL", "Docker"],
        "experiences": [
            {
                "role": "Engenheiro de Software Senior",
                "company": "Tech Solutions Corp",
                "period": "Jan 2022 - Presente",
                "highlights": [
                    "Liderou arquitetura de microservicos em Java 21 atendendo +1M requisicoes diarias.",
                    "Implementou orquestracao de agentes IA reduzindo o tempo de resposta em 40%."
                ]
            },
            {
                "role": "Desenvolvedor Backend Fullstack",
                "company": "DataAutomate Inc",
                "period": "Mar 2020 - Dez 2021",
                "highlights": [
                    "Desenvolveu automacoes de extracao de dados com Python e Playwright.",
                    "Construiu pipelines de integracao continua e APIs REST em Java."
                ]
            }
        ]
    }

    pdf_path = generator.generate_pdf(sample_resume, "curriculo_joao_silva_ats.pdf")
    print(f"\n--- PDF Gerado com Sucesso ---")
    print(f"Caminho do arquivo: {pdf_path}")


if __name__ == "__main__":
    main()
