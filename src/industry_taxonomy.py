"""
Módulo de Taxonomia de Setores e Indústrias (Industry Taxonomy Engine)
JobAutomator AI - Suporte Universal para Múltiplas Profissões.
Mapeia regras de ATS, palavras-chave de alto valor, certificações mandatórias,
KPIs/métricas esperadas e verbos de ação para qualquer setor do mercado.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("IndustryTaxonomy")

# Catálogo central de indústrias e padrões de mercado
TAXONOMY_CATALOG: Dict[str, Dict[str, Any]] = {
    "FINANCE_ASSET_MANAGEMENT": {
        "display_name": "Mercado Financeiro / Asset Management & Banking",
        "keywords_mandatory": [
            "AUM (Assets Under Management)", "Valuation DCF", "Analise Fundamentalista",
            "Gestao de Risco", "Alocacao de Ativos", "Indice Sharpe", "Sortino Ratio",
            "Modern Portfolio Theory (MPT)", "Modelagem Financeira em Python/VBA",
            "Compliance CVM / BACEN / ANBIMA", "Mercado de Capitais", "Derivativos e Hedge Cambial"
        ],
        "categorized_skills": {
            "Valuation & Modelagem": ["Valuation DCF", "WACC", "FCD", "Analise de Sensibilidade", "LBO", "M&A"],
            "Analise Quantitativa & Risco": ["VaR", "CVaR", "Indice Sharpe", "Sortino", "Maximo Drawdown", "GARCH", "Stress Testing", "Backtesting"],
            "Alocacao de Ativos": ["Modern Portfolio Theory (MPT)", "Rebalanceamento Tatico", "Asset-Liability Management (ALM)", "Renda Fixa e Variavel"],
            "Programacao & Dados": ["Python (Pandas, NumPy)", "VBA Avancado", "SQL", "APIs Bloomberg / Refinitiv", "Economatica"],
            "Lideranca & Soft Skills": ["Gestao de Equipes Multidisciplinares", "Comunicacao Executiva com Board e C-Level", "Apresentacao a Investidores Institucionais", "Negociacao com Custodiantes"]
        },
        "certifications_standard": [
            "CFA Level III (Chartered Financial Analyst) - CFA Institute",
            "CGA (Certificacao de Gestores ANBIMA)",
            "CEA (Certificacao de Especialista em Investimentos ANBIMA)",
            "CNPI (Certificado Nacional do Profissional de Investimento)",
            "CPA-20 (ANBIMA)"
        ],
        "tools_and_systems": [
            "Bloomberg Terminal", "Refinitiv Eikon", "Economatica", "Excel Avancado (VBA/Python)",
            "Enfusion", "Sinacor", "Power BI", "Tableau"
        ],
        "kpi_metrics_templates": [
            "Carteira sob gestao (AUM) de R$ {N}M",
            "Retorno anualizado de {N}% do CDI / Ibovespa",
            "Indice Sharpe de {N}",
            "Reducao de VaR (Value at Risk) em {N}%",
            "Economia de tempo de analise de {N}h/dia para {N}min/dia ({N}% ganho de eficiencia)"
        ],
        "action_verbs": [
            "Estruturou", "Alocou", "Modelou", "Gerenciou", "Maximizou", "Mitigou", "Auditorou", "Liderou"
        ]
    },
    "HEALTHCARE_MEDICAL": {
        "display_name": "Saúde / Medicina & Especialidades Hospitalares",
        "keywords_mandatory": [
            "CRM e RQE de Especialidade", "Medicina Baseada em Evidencias", "Protocolos Clinicos",
            "Atendimento de Alta Complexidade", "Terapia Intensiva e Urgencia", "Monitorizacao Hemodinamica",
            "Auditoria Assistencial", "Manejo Farmacologico", "Desospitalizacao Segura"
        ],
        "certifications_standard": [
            "Titulo de Especialista (AMB / Conselho de Especialidade)",
            "ACLS (Advanced Cardiovascular Life Support - AHA)",
            "ATLS (Advanced Trauma Life Support)",
            "BLS (Basic Life Support)",
            "FCCS (Fundamental Critical Care Support)"
        ],
        "tools_and_systems": [
            "MV Soul", "Tasy (Philips)", "Epimed Monitor", "Soul MV", "CROSS / Regulacao",
            "Prontuario Eletronico do Paciente (PEP)"
        ],
        "kpi_metrics_templates": [
            "Taxa de sobrevida de {N}% em quadros criticos",
            "Tempo porta-balao / porta-eletrocardiograma reduzido para {N} min",
            "Mais de {N} atendimentos de urgencia com complicacao <{N}%",
            "Reducao do tempo medio de internacao (LOS) em {N}%"
        ],
        "action_verbs": [
            "Prescreveu", "Liderou", "Estabilizou", "Implementou", "Diagnosticou", "Coordenou", "Conduziu", "Preceptou"
        ]
    },
    "FOOD_BAKERY_GASTRONOMY": {
        "display_name": "Alimentos & Gastronomia / Panificação & Confeitaria Industrial",
        "keywords_mandatory": [
            "Fermentacao Natural (Levain / Sourdough)", "Boas Praticas de Fabricacao (BPF / ANVISA)",
            "Ficha Tecnica Operacional", "Controle de CMV (Custo de Mercadoria Vendida)",
            "Gestao de Estoque e Validade (FIFO/PEPS)", "Controle de Perdas e Quebra",
            "Padronizacao de Receitas", "Controle Microbiologico e Higiene"
        ],
        "certifications_standard": [
            "Certificacao em Boas Praticas de Fabricacao (BPF / ANVISA)",
            "Formacao Profissional em Panificacao e Confeitaria (SENAI / Le Cordon Bleu)",
            "Curso de Manipulacao Higienico-Sanitaria de Alimentos",
            "Gestao de Cozinhas e Custos Gastronomicos"
        ],
        "tools_and_systems": [
            "Forno de Lastro e Conveccao", "Amassadeira Espiral e Planetaria", "Camara de Fermentacao Controlada",
            "Sistemas ERP de Restaurante / Padaria (Totvs Chef, Colibri, Saipos)", "Planilhas de CMV e Ficha Tecnica"
        ],
        "kpi_metrics_templates": [
            "Producao diaria de {N}kg de panificados artesanais",
            "Reducao de desperdicio de materia-prima de {N}% para {N}%",
            "Margem de contribuicao do setor elevada em {N}%",
            "100% de conformidade em auditorias sanitarias municipais e estaduais"
        ],
        "action_verbs": [
            "Desenvolveu", "Padronizou", "Produziu", "Otimizou", "Capacitou", "Adequou", "Coordenou", "Formulou"
        ]
    },
    "SOFTWARE_TECH_AI": {
        "display_name": "Tecnologia / Engenharia de Software & IA",
        "keywords_mandatory": [
            "Programacao Reativa e Concorrencia", "Microsservicos Distribuidos", "Arquitetura Limpa (Clean Arch)",
            "Filas e Mensageria (Kafka/RabbitMQ)", "Bancos de Dados Relacionais e NoSQL", "CI/CD e DevOps",
            "APIs RESTful e gRPC", "Testes Automatizados", "Alta Disponibilidade e Escalabilidade"
        ],
        "certifications_standard": [
            "AWS Certified Solutions Architect",
            "Google Cloud Professional Data / Cloud Engineer",
            "Certified Kubernetes Administrator (CKA)",
            "Oracle Certified Professional Java Developer"
        ],
        "tools_and_systems": [
            "Docker / Kubernetes", "Git / GitHub Actions", "PostgreSQL / MongoDB", "Kafka / Redis",
            "Datadog / Prometheus / Grafana", "Linux / Bash"
        ],
        "kpi_metrics_templates": [
            "Throughput de {N} requisicoes por segundo suportado",
            "Latencia p99 reduzida em {N}% sob carga de pico",
            "Cobertura de testes automatizados elevada para {N}%",
            "Uptime de {N}% mantido em sistemas de missao critica"
        ],
        "action_verbs": [
            "Arquitetou", "Implementou", "Refatorou", "Automatizou", "Otimizou", "Escalou", "Projetou", "Integrou"
        ]
    },
    "CIVIL_ENGINEERING_CONSTRUCTION": {
        "display_name": "Engenharia Civil / Gerenciamento de Obras & Infraestrutura",
        "keywords_mandatory": [
            "CREA Ativo com ART", "Gerenciamento de Obras", "Planejamento e Orcamento (SINAPI / TCPO)",
            "Metodologia BIM", "Normas Regulamentadoras (NR-18, NR-35)", "Controle Tecnologico do Concreto",
            "Lean Construction", "Cronograma Fisico-Financeiro", "Gestao de Empreiteiros e Fornecedores"
        ],
        "certifications_standard": [
            "CREA (Conselho Regional de Engenharia e Agronomia) com ARTs comprovadas",
            "PMP (Project Management Professional - PMI)",
            "Certificacao em Modelagem BIM (Autodesk)",
            "Auditor Interno PBQP-H / ISO 9001"
        ],
        "tools_and_systems": [
            "AutoCAD / Revit (BIM)", "MS Project / Primavera P6", "Sienge / Mega Sistemas",
            "Volare / OrçaFascio", "Navisworks"
        ],
        "kpi_metrics_templates": [
            "Gestao de obras de {N} mil m² de area construida",
            "Entrega de empreendimento com {N}% abaixo do orcamento estimado",
            "Cumprimento de {N}% do cronograma fisico-financeiro sem desvios criticos",
            "Zero acidentes com afastamento (LTI) em {N} mil horas-homem trabalhadas"
        ],
        "action_verbs": [
            "Gerenciou", "Fiscalizou", "Orcou", "Planejou", "Compatibilizou", "Coordenou", "Entregou", "Adequou"
        ]
    }
}


class IndustryTaxonomyEngine:
    """
    Motor central de taxonomia que identifica a indústria da vaga ou do profissional
    e fornece o kit completo de keywords, métricas e verbos de impacto.
    """

    def __init__(self):
        self.catalog = TAXONOMY_CATALOG

    def detect_industry(self, job_title: str, text_context: str = "") -> str:
        """
        Classifica a indústria com base no título e no contexto da vaga.
        """
        combined = f"{job_title} {text_context}".lower()

        if any(w in combined for w in ["asset", "portfolio", "banker", "investimento", "aum", "sharpe", "fundo", "trader", "cvm", "cfa", "cga"]):
            return "FINANCE_ASSET_MANAGEMENT"
        elif any(w in combined for w in ["medico", "medica", "crm", "rqe", "cardiolog", "intensiv", "hospital", "clinica", "uti", "enfermaria"]):
            return "HEALTHCARE_MEDICAL"
        elif any(w in combined for w in ["padeiro", "panificacao", "confeitaria", "sourdough", "fermentacao", "pao", "baker", "gastronomia", "cozinha"]):
            return "FOOD_BAKERY_GASTRONOMY"
        elif any(w in combined for w in ["civil", "obra", "edificacoes", "crea", "sinapi", "construcao", "bim", "revit", "canteiro"]):
            return "CIVIL_ENGINEERING_CONSTRUCTION"
        elif any(w in combined for w in ["software", "desenvolvedor", "backend", "frontend", "java", "python", "fullstack", "devops", "cloud", "ia", "tech"]):
            return "SOFTWARE_TECH_AI"

        # Fallback para software se não identificado
        return "SOFTWARE_TECH_AI"

    def get_taxonomy_pack(self, industry_key: str) -> Dict[str, Any]:
        """
        Retorna as regras e banco de termos para o setor solicitado.
        """
        return self.catalog.get(industry_key, self.catalog["SOFTWARE_TECH_AI"])

    def enrich_unknown_industry_via_ai(self, profession_title: str, job_description: str) -> Dict[str, Any]:
        """
        Para profissões exóticas ou não catalogadas, utiliza o modelo NVIDIA Nemotron
        para gerar o kit de taxonomia correspondente sob demanda.
        """
        try:
            from ai_service import NvidiaAIService
            ai_service = NvidiaAIService()

            prompt = (
                f"Você é um arquiteto sênior de dados de recrutamento e taxonomia de carreiras.\n"
                f"Profissão: {profession_title}\n"
                f"Contexto: {job_description}\n\n"
                f"Gere o pacote de taxonomia completo para esta profissão em JSON estrito:\n"
                f"{{\n"
                f'  "display_name": "<Nome da Indústria>",\n'
                f'  "keywords_mandatory": ["<8 a 10 termos tecnicos obrigatorios>"],\n'
                f'  "certifications_standard": ["<3 a 5 certificacoes ou licencas essenciais>"],\n'
                f'  "tools_and_systems": ["<4 a 6 softwares ou equipamentos padrao da industria>"],\n'
                f'  "kpi_metrics_templates": ["<3 formulas de impacto quantificavel>"],\n'
                f'  "action_verbs": ["<6 verbos de comando fortes>"]\n'
                f"}}"
            )

            completion = ai_service.client.chat.completions.create(
                model=ai_service.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente de taxonomia de dados de carreira. Retorne apenas JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2048,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 1024},
                stream=False
            )

            raw_text = completion.choices[0].message.content or ""
            parsed = ai_service._extract_json(raw_text)
            return parsed
        except Exception as e:
            logger.error(f"Falha ao enriquecer taxonomia via IA: {e}")
            return self.get_taxonomy_pack("SOFTWARE_TECH_AI")


if __name__ == "__main__":
    engine = IndustryTaxonomyEngine()
    print("=== TESTE DE TAXONOMIA DE INDÚSTRIAS ===")
    
    test_titles = [
        "Senior Asset Manager (Fundos Multimercado)",
        "Padeiro Artesanal Especialista em Sourdough",
        "Engenheiro Civil Residente de Obra Predial",
        "Médica Plantonista de Terapia Intensiva",
        "Tech Lead Java Reativo & Cloud"
    ]

    for title in test_titles:
        ind = engine.detect_industry(title)
        pack = engine.get_taxonomy_pack(ind)
        print(f"\nCargo: {title}")
        print(f"  -> Setor Identificado: {pack['display_name']}")
        print(f"  -> Top Keywords: {', '.join(pack['keywords_mandatory'][:4])}")
        print(f"  -> Certificações Padrão: {', '.join(pack['certifications_standard'][:2])}")
