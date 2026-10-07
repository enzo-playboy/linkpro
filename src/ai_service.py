"""
AI Service - JobAutomator AI
Connects to NVIDIA NIM API (Nemotron 3.5 Lightning with reasoning)
Upgraded with principles from the 'resume-tailoring-skill':
- Truth-preserving optimization (never fabricate experience)
- Weighted 4-pillar matching (Direct 40%, Transferable 30%, Adjacent 20%, Impact 10%)
- Content reframing (Keyword Alignment, Emphasis Shift, Scope Clarification)
- Branching gap questions to surface undocumented skills
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("AIService")

NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")


class NvidiaAIService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or NVIDIA_API_KEY or os.getenv("OPENAI_API_KEY", "") or "dummy-key"
        self.base_url = base_url or NVIDIA_BASE_URL
        self.model = model or NVIDIA_MODEL
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extracts JSON from LLM output, handling markdown blocks and preambles."""
        text = text.strip()
        # Look for JSON between code fences first
        code_fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if code_fence_match:
            try:
                return json.loads(code_fence_match.group(1).strip())
            except Exception:
                pass
        
        # Look for outermost curly braces
        curly_match = re.search(r"(\{[\s\S]*\})", text)
        if curly_match:
            try:
                return json.loads(curly_match.group(1).strip())
            except Exception:
                pass

        # Direct parse attempt
        return json.loads(text)

    def evaluate_job_match(
        self,
        job_title: str,
        job_description: str,
        candidate_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Uses NVIDIA Nemotron model with reasoning enabled to audit ATS match score (0-100),
        applying the weighted 4-pillar matching algorithm:
        - Direct Match (40%): exact keywords & technologies
        - Transferable Skills (30%): same capability in different context
        - Adjacent Experience (20%): related tools and frameworks
        - Impact Alignment (10%): metrics, scale, and business outcomes
        """
        logger.info(f"Enviando requisicao para NVIDIA Nemotron ({self.model}) para avaliar vaga: {job_title}")

        prompt = (
            f"Você é um auditor sênior de recrutamento e especialista em ATS, utilizando a metodologia do 'Resume Tailoring Skill'.\n\n"
            f"VAGA ALVO:\n"
            f"Título: {job_title}\n"
            f"Descrição e Requisitos: {job_description}\n\n"
            f"PERFIL DO CANDIDATO:\n"
            f"Nome: {candidate_profile.get('full_name')}\n"
            f"Habilidades: {', '.join(candidate_profile.get('skills', []))}\n"
            f"Resumo: {candidate_profile.get('summary', '')}\n\n"
            f"REGRAS DE AVALIAÇÃO:\n"
            f"1. Princípio Fundamental: Preservação estrita da verdade (NUNCA invente ou assuma experiências falsas).\n"
            f"2. Calcule os 4 pilares ponderados:\n"
            f"   - direct_match (peso 40%): sobreposição exata de tecnologias e requisitos obrigatórios (0 a 100)\n"
            f"   - transferable_skills (peso 30%): habilidades transferíveis para o mesmo objetivo (0 a 100)\n"
            f"   - adjacent_experience (peso 20%): ferramentas correlatas ou experiência em ecossistema próximo (0 a 100)\n"
            f"   - impact_alignment (peso 10%): alinhamento de métricas, escala e impacto (0 a 100)\n"
            f"3. Calcule o 'overall_score' ponderado: (direct * 0.4) + (transferable * 0.3) + (adjacent * 0.2) + (impact * 0.1)\n"
            f"4. Classifique a faixa de confiança ('DIRECT' >= 90, 'TRANSFERABLE' 75-89, 'ADJACENT' 60-74, 'WEAK' 45-59, 'GAP' < 45)\n"
            f"5. Se houver gaps (<60%), gere 'branching_questions' para descobrir se o candidato já trabalhou com isso informalmente.\n\n"
            f"Retorne OBRIGATORIAMENTE um JSON estrito nesta estrutura exata:\n"
            f"{{\n"
            f'  "overall_score": <float 0 a 100>,\n'
            f'  "confidence_band": "DIRECT" | "TRANSFERABLE" | "ADJACENT" | "WEAK" | "GAP",\n'
            f'  "pillar_scores": {{\n'
            f'    "direct_match": <0-100>,\n'
            f'    "transferable_skills": <0-100>,\n'
            f'    "adjacent_experience": <0-100>,\n'
            f'    "impact_alignment": <0-100>\n'
            f'  }},\n'
            f'  "justification": "<análise técnica e estratégica>",\n'
            f'  "matched_keywords": ["<str>"],\n'
            f'  "missing_keywords": ["<str>"],\n'
            f'  "reframing_suggestions": ["<sugestão de alinhamento de termos sem mentir>"],\n'
            f'  "branching_questions": ["<pergunta para extrair experiência não documentada>"],\n'
            f'  "recommendation": "APROVADO_PARA_CANDIDATURA" | "REQUER_AJUSTE" | "REPROVADO"\n'
            f"}}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em ATS e Resume Tailoring. Retorne apenas JSON estrito válido sem marcadores de markdown extras."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                top_p=0.95,
                max_tokens=4096,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 2048},
                stream=True
            )

            reasoning_accum = []
            content_accum = []

            for chunk in completion:
                if not chunk.choices:
                    continue
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    reasoning_accum.append(reasoning)
                if chunk.choices[0].delta.content:
                    content_accum.append(chunk.choices[0].delta.content)

            reasoning_text = "".join(reasoning_accum)
            content_text = "".join(content_accum).strip()

            parsed = self._extract_json(content_text)

            return {
                "status": "SUCCESS",
                "model": self.model,
                "reasoning_log": reasoning_text,
                "data": parsed
            }

        except Exception as e:
            logger.error(f"Erro ao consultar NVIDIA API: {e}", exc_info=True)
            return {
                "status": "ERROR",
                "error": str(e),
                "model": self.model
            }

    def tailor_resume_content(
        self,
        job_title: str,
        job_description: str,
        candidate_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applies truth-preserving reframing to experiences and generates an optimized cover letter.
        """
        logger.info(f"Executando Tailoring e Reframing com NVIDIA Nemotron para: {job_title}")

        prompt = (
            f"Você é um redator sênior de currículos e cartas de apresentação executivas.\n"
            f"Metodologia: 'Truth-Preserving Optimization' (alinhar terminologia, destacar impactos relevantes sem inventar informações).\n\n"
            f"VAGA:\n"
            f"Título: {job_title}\n"
            f"Contexto: {job_description}\n\n"
            f"CANDIDATO:\n"
            f"Nome: {candidate_profile.get('full_name')}\n"
            f"Habilidades: {', '.join(candidate_profile.get('skills', []))}\n"
            f"Resumo Atual: {candidate_profile.get('summary')}\n\n"
            f"TAREFAS:\n"
            f"1. Crie um 'tailored_summary' (Resumo Profissional Reescrito) de 3 a 4 linhas, otimizado para a vaga.\n"
            f"2. Escreva uma 'cover_letter' profissional e persuasiva de 2 a 3 parágrafos em Português.\n\n"
            f"Retorne OBRIGATORIAMENTE em JSON estrito:\n"
            f"{{\n"
            f'  "tailored_summary": "<resumo profissional adaptado>",\n'
            f'  "cover_letter": "<carta de apresentação completa>",\n'
            f'  "reframing_notes": "<explicação de quais termos foram alinhados>"\n'
            f"}}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente de carreira. Retorne apenas JSON estrito válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                top_p=0.95,
                max_tokens=4096,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 2048},
                stream=True
            )

            content_accum = []
            reasoning_accum = []
            for chunk in completion:
                if not chunk.choices:
                    continue
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    reasoning_accum.append(reasoning)
                if chunk.choices[0].delta.content:
                    content_accum.append(chunk.choices[0].delta.content)

            content_text = "".join(content_accum).strip()
            parsed = self._extract_json(content_text)

            return {
                "status": "SUCCESS",
                "data": parsed,
                "reasoning_log": "".join(reasoning_accum)
            }
        except Exception as e:
            logger.error(f"Erro ao executar Tailoring com NVIDIA: {e}", exc_info=True)
            return {
                "status": "ERROR",
                "error": str(e)
            }
