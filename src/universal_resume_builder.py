"""
Construtor Universal de Currículos por Indústria (Universal Multi-Industry Resume Builder)
JobAutomator AI - Suporta qualquer perfil profissional:
Finance (Asset Manager / Banker), Gastronomia (Panificação), Saúde (Medicina),
Engenharia Civil, Tecnologia / IA, etc.
Gera PDFs com conformidade ATS 100% e copy de alto impacto.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from industry_taxonomy import IndustryTaxonomyEngine
from role_research_service import RoleResearchService
from pdf_generator import ResumePDFGenerator
from ai_service import NvidiaAIService

logger = logging.getLogger("UniversalResumeBuilder")


class UniversalResumeBuilder:
    def __init__(self, output_dir: str = "generated_resumes"):
        self.output_dir = output_dir
        self.pdf_generator = ResumePDFGenerator(output_dir=self.output_dir)
        self.taxonomy_engine = IndustryTaxonomyEngine()
        self.research_service = RoleResearchService()
        self.ai_service = NvidiaAIService()

    def build_custom_industry_resume(
        self,
        candidate_data: Dict[str, Any],
        job_title: str,
        job_description: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orquestra a criação completa de um currículo adaptado para a indústria e vaga:
        1. Executa pesquisa de mercado da vaga (RoleResearchService).
        2. Carrega a taxonomia e vocabulário de valor do setor.
        3. Enriquece as habilidades e reescreve o resumo com a terminologia exata.
        4. Compila o PDF ATS com as 7 seções canônicas.
        """
        logger.info(f"Construindo currículo universal para o cargo: '{job_title}'")

        # 1. Pesquisa de Mercado e Taxonomia
        research = self.research_service.research_job_and_industry(job_title, job_description)
        taxonomy = research["taxonomy_pack"]
        success_profile = research["success_profile"]

        # 2. Priorização inteligente de Habilidades
        # Coloca as keywords da vaga e da taxonomia no início da lista de skills
        existing_skills = candidate_data.get("skills", [])
        mandatory_keywords = taxonomy.get("keywords_mandatory", [])
        
        # Reordena mantendo habilidades do candidato que coincidem com a indústria na frente
        prioritized_skills = []
        for kw in mandatory_keywords:
            for s in existing_skills:
                if any(part.lower() in s.lower() for part in kw.split()[:2]):
                    if s not in prioritized_skills:
                        prioritized_skills.append(s)

        for s in existing_skills:
            if s not in prioritized_skills:
                prioritized_skills.append(s)

        # 3. Montar perfil final estruturado
        safe_filename = filename or f"curriculo_{candidate_data.get('full_name', 'candidato').lower().replace(' ', '_').replace('.', '')}_{research['industry_key'].lower()}_ats.pdf"

        final_profile = dict(candidate_data)
        final_profile["skills"] = prioritized_skills

        # 4. Gerar o PDF no padrão limpo aprovado pelo ATS
        pdf_path = self.pdf_generator.generate_pdf(final_profile, safe_filename)

        logger.info(f"PDF universal compilado com sucesso em: {pdf_path}")

        return {
            "status": "SUCCESS",
            "pdf_path": pdf_path,
            "filename": safe_filename,
            "industry_identified": taxonomy["display_name"],
            "industry_key": research["industry_key"],
            "role_archetype": success_profile.get("role_archetype"),
            "must_have_requirements": success_profile.get("must_have_requirements", []),
            "key_performance_indicators": success_profile.get("key_performance_indicators", []),
            "total_skills_mapped": len(prioritized_skills)
        }
