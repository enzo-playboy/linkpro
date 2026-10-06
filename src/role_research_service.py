"""
Agente de Pesquisa de Mercado e Vagas (Role & Industry Research Agent)
JobAutomator AI - Baseado nas diretrizes do 'resume-tailoring-skill'.
Analisa descrições de vagas, sintetiza perfis de sucesso (Success Profile),
mapeia terminologia corporativa e identifica os requisitos críticos do setor.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from industry_taxonomy import IndustryTaxonomyEngine
from ai_service import NvidiaAIService

logger = logging.getLogger("RoleResearchService")


class RoleResearchService:
    def __init__(self):
        self.taxonomy_engine = IndustryTaxonomyEngine()
        self.ai_service = NvidiaAIService()

    def research_job_and_industry(self, job_title: str, job_description: str) -> Dict[str, Any]:
        """
        Executa pesquisa aprofundada da vaga e do setor:
        1. Identifica a indústria e carrega o pacote de taxonomia correspondente.
        2. Analisa os requisitos explícitos e implícitos da vaga.
        3. Mapeia o vocabulário preferido da empresa e os KPIs exigidos.
        4. Gera o 'Success Profile' para guiar a confecção do currículo.
        """
        logger.info(f"Iniciando pesquisa de mercado para a vaga: '{job_title}'")

        # 1. Detectar indústria
        industry_key = self.taxonomy_engine.detect_industry(job_title, job_description)
        taxonomy_pack = self.taxonomy_engine.get_taxonomy_pack(industry_key)

        # 2. Sintetizar Success Profile com NVIDIA Nemotron
        prompt = (
            f"Você é um Headhunter Sênior e Especialista em Pesquisa de Mercado de Carreiras.\n"
            f"Vaga Alvo: {job_title}\n"
            f"Descrição da Vaga: {job_description}\n"
            f"Indústria Identificada: {taxonomy_pack['display_name']}\n"
            f"Padrões de Referência do Setor:\n"
            f"- Keywords comuns: {', '.join(taxonomy_pack['keywords_mandatory'][:6])}\n"
            f"- Certificações comuns: {', '.join(taxonomy_pack['certifications_standard'][:3])}\n\n"
            f"TAREFA:\n"
            f"Sintetize o 'Perfil de Sucesso' (Success Profile) para este cargo em JSON estrito com esta estrutura:\n"
            f"{{\n"
            f'  "role_archetype": "<Liderança Técnica | Especialista Individual | Gestão Operacional>",\n'
            f'  "must_have_requirements": ["<requisito 1>", "<requisito 2>"],\n'
            f'  "nice_to_have_capabilities": ["<diferencial 1>", "<diferencial 2>"],\n'
            f'  "key_performance_indicators": ["<métrica esperada 1>", "<métrica esperada 2>"],\n'
            f'  "terminology_map": {{\n'
            f'    "termo_genérico": "termo_específico_valorizado_pela_vaga"\n'
            f'  }},\n'
            f'  "cultural_signals": ["<sinal cultural valorizado>"],\n'
            f'  "red_flags_to_avoid": ["<o que o recrutador detesta ver no currículo>"]\n'
            f"}}"
        )

        try:
            completion = self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": "Você é um consultor sênior de recrutamento. Retorne apenas JSON estrito válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                top_p=0.95,
                max_tokens=4096,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 2048},
                stream=False
            )

            raw_text = completion.choices[0].message.content or ""
            parsed = self.ai_service._extract_json(raw_text)

            result = {
                "status": "SUCCESS",
                "job_title": job_title,
                "industry_key": industry_key,
                "industry_name": taxonomy_pack["display_name"],
                "taxonomy_pack": taxonomy_pack,
                "success_profile": parsed
            }

            logger.info(f"Pesquisa de mercado concluída com sucesso para indústria: {taxonomy_pack['display_name']}")
            return result

        except Exception as e:
            logger.error(f"Erro na pesquisa de mercado com IA: {e}", exc_info=True)
            # Fallback estruturado
            return {
                "status": "FALLBACK",
                "job_title": job_title,
                "industry_key": industry_key,
                "industry_name": taxonomy_pack["display_name"],
                "taxonomy_pack": taxonomy_pack,
                "success_profile": {
                    "role_archetype": "Especialista Técnico",
                    "must_have_requirements": taxonomy_pack["keywords_mandatory"][:4],
                    "nice_to_have_capabilities": taxonomy_pack["certifications_standard"][:2],
                    "key_performance_indicators": taxonomy_pack["kpi_metrics_templates"][:2],
                    "terminology_map": {},
                    "cultural_signals": ["Foco em resultados e rigor técnico"],
                    "red_flags_to_avoid": ["Experiência genérica sem dados mensuráveis"]
                }
            }


if __name__ == "__main__":
    service = RoleResearchService()
    test_title = "Portfolio & Asset Allocation Manager"
    test_desc = "Buscamos gestor de portfólio para fundos multimercado com foco em renda variável e crédito privado. Exigido CGA/CFA, forte modelagem em Excel/Python e Bloomberg."
    
    res = service.research_job_and_industry(test_title, test_desc)
    print("=== RESULTADO DA PESQUISA DE MERCADO ===")
    print(f"Setor: {res['industry_name']}")
    print(f"Arquétipo: {res['success_profile'].get('role_archetype')}")
    print("Requisitos Críticos:", res['success_profile'].get('must_have_requirements'))
    print("KPIs Esperados:", res['success_profile'].get('key_performance_indicators'))
