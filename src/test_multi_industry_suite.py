"""
Bateria de Testes Automatizada Multi-Indústria (Multi-Industry Test Suite)
JobAutomator AI - Validação de Taxonomia, Pesquisa e Geração de Currículos para:
1. Mercado Financeiro / Asset Management
2. Alimentos & Panificação Artesanal
3. Engenharia Civil / Gerenciamento de Obras
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import pypdf

from universal_resume_builder import UniversalResumeBuilder

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
REPORT_FILE = os.path.join(LOG_DIR, "multi_industry_test_report.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MultiIndustryTestSuite")


def run_multi_industry_tests():
    builder = UniversalResumeBuilder()
    test_results = []

    # =========================================================================
    # CASO 1: MERCADO FINANCEIRO (ASSET MANAGER / PORTFOLIO MANAGER)
    # =========================================================================
    logger.info(">>> TESTE 1: MERCADO FINANCEIRO (ASSET MANAGEMENT) <<<")
    finance_candidate = {
        "full_name": "Rodrigo Siqueira Bueno",
        "email": "rodrigo.bueno@capitalpartners.com.br",
        "phone": "+55 (11) 98111-2233",
        "location": "Sao Paulo, SP - Brasil",
        "summary": (
            "Portfolio Manager e Asset Allocator com 10 anos de experiencia em gestao discricionaria de fundos "
            "multimercado e renda variavel. Especialista em modelagem macroeconomica, valuation DCF e gestao quantitativa "
            "de risco (VaR, Drawdown e Sharpe). Historico de geracao de alpha consistente com compliance estrito perante CVM e ANBIMA."
        ),
        "skills": [
            "AUM (Assets Under Management)", "Valuation DCF", "Analise Fundamentalista", "Gestao de Risco",
            "Alocacao de Ativos", "Indice Sharpe", "Modelagem Financeira em Python/VBA", "Bloomberg Terminal",
            "Refinitiv Eikon", "Economatica", "Compliance CVM / BACEN", "Mercado de Capitais"
        ],
        "experiences": [
            {
                "role": "Lead Portfolio Manager (Fundos Multimercado)",
                "company": "Vinci Capital Partners",
                "period": "Jan 2021 - Presente",
                "highlights": [
                    "AUM sob gestao direta: R$ 580M | Retorno acumulado: 124% do CDI | Indice Sharpe: 1.48.",
                    "Estruturou estratégias sistemáticas de hedge cambial e taxas de juros, reduzindo o drawdown máximo em 32% durante choques de volatilidade.",
                    "Liderou comite semanal de investimentos e relatorios de alocacao para mais de 1.200 cotistas institucionais e private."
                ]
            },
            {
                "role": "Analista Senior de Equity Research & Risco",
                "company": "Itaú BBA / Asset Management",
                "period": "Mar 2016 - Dez 2020",
                "highlights": [
                    "Cobertura ativa de 18 empresas do setor de commodities e varejo com emissao de relatorios proprietarios de recomendacao.",
                    "Desenvolveu pipeline automatizado em Python integrado a API do Bloomberg para analise de demonstracoes financeiras em tempo real."
                ]
            }
        ],
        "education": [
            {
                "degree": "Mestrado Profissional em Economia e Financas",
                "institution": "Fundacao Getulio Vargas (FGV-EESP)",
                "period": "2018 - 2020",
                "details": "Dissertacao em Alocacao Dinamica de Portfolios e Modelos GARCH"
            },
            {
                "degree": "Bacharelado em Engenharia de Producao",
                "institution": "Escola Politecnica da USP (Poli-USP)",
                "period": "2011 - 2015",
                "details": "Enfase em Pesquisa Operacional e Estatistica Aplicada"
            }
        ],
        "certifications": [
            "CFA (Chartered Financial Analyst) - CFA Institute (Ativo desde 2019)",
            "CGA (Certificacao de Gestores ANBIMA) - ANBIMA (Ativo desde 2020)",
            "CNPI (Certificado Nacional do Profissional de Investimento) - APIMEC",
            "ANBIMA CEA (Especialista em Investimentos)"
        ],
        "publications": [
            "BUENO, R. S. Impacto da Assimetria de Volatilidade na Otimizacao de Portfolios Brasileiros. Revista Brasileira de Financas, 2021."
        ],
        "languages": [
            {"language": "Portugues", "proficiency": "Nativo"},
            {"language": "Ingles", "proficiency": "Fluente (C2 - TOEFL 115)"},
            {"language": "Espanhol", "proficiency": "Avancado (B2)"}
        ]
    }

    finance_job = {
        "title": "Senior Portfolio & Asset Allocation Manager",
        "description": "Buscamos gestor senior com CFA/CGA para liderar carteiras multimercado e gerir mais de R$ 300M em AUM. Forte experiencia em Bloomberg, Python e modelos de Sharpe."
    }

    res_finance = builder.build_custom_industry_resume(
        finance_candidate,
        finance_job["title"],
        finance_job["description"],
        "curriculo_rodrigo_bueno_finance_ats.pdf"
    )
    test_results.append(audit_and_evaluate(res_finance, "FINANCE_ASSET_MANAGEMENT"))

    # =========================================================================
    # CASO 2: ALIMENTOS & GASTRONOMIA (PANIFICAÇÃO ARTESANAL & INDUSTRIAL)
    # =========================================================================
    logger.info(">>> TESTE 2: ALIMENTOS & GASTRONOMIA (PANIFICACAO) <<<")
    bakery_candidate = {
        "full_name": "Chef Matheus Oliveira Ramos",
        "email": "matheus.ramos.chef@panificacao.com.br",
        "phone": "+55 (11) 97222-3344",
        "location": "Sao Paulo, SP - Brasil",
        "summary": (
            "Mestre Padeiro e Especialista em Panificacao Artesanal e Industrial com 9 anos de carreira. "
            "Expert em fermentacao natural (levain/sourdough), desenvolvimento de fichas tecnicas operacionais, "
            "controle rigoroso de CMV e gestao de perdas de insumos. Experiencia comprovada em adequacao total as Boas "
            "Praticas de Fabricacao (BPF) da ANVISA e lideranca de brigadas de producao em alta escala."
        ),
        "skills": [
            "Fermentacao Natural (Levain / Sourdough)", "Boas Praticas de Fabricacao (BPF / ANVISA)",
            "Ficha Tecnica Operacional", "Controle de CMV (Custo de Mercadoria Vendida)",
            "Gestao de Estoque (FIFO/PEPS)", "Controle de Perdas e Quebra", "Padronizacao de Receitas",
            "Operacao de Fornos de Lastro e Conveccao", "Amassadeiras Espirais Industriais", "Gestao de Equipes de Cozinha"
        ],
        "experiences": [
            {
                "role": "Chef Padeiro / Chefe de Producao",
                "company": "Padaria & Empório Artesanal Santo Pão",
                "period": "Fev 2021 - Presente",
                "highlights": [
                    "Volume diario: 480kg de panificados artesanais | Desperdicio reduzido de 12% para 3,4% | Margem do setor ampliada em 22%.",
                    "Criou e padronizou 28 fichas tecnicas com precificacao dinamica e controle de custo de materia-prima por grama.",
                    "Treinou e liderou equipe de 10 auxiliares e padeiros, alcancando 100% de conformidade em inspecoes da Vigilancia Sanitaria."
                ]
            },
            {
                "role": "Padeiro Encarregado de Forno e Massas",
                "company": "Indústria de Panificação Forno Nobre",
                "period": "Abr 2016 - Jan 2021",
                "highlights": [
                    "Gerenciou linhas de fornadas em fornos de lastro continuos atendendo rede com 14 pontos de distribuicao.",
                    "Implantou sistema FIFO para controle de farinhas e fermentos, zerando descartes por prazo de validade."
                ]
            }
        ],
        "education": [
            {
                "degree": "Formacao Profissional de Mestre Padeiro e Confeiteiro",
                "institution": "Escola SENAI de Confeitaria e Panificacao",
                "period": "2015 - 2016",
                "details": "Carga horaria: 1.200h com especializacao em biologia de leveduras"
            },
            {
                "degree": "Tecnologo em Gastronomia",
                "institution": "Centro Universitario Senac SP",
                "period": "2013 - 2015",
                "details": "Foco em Gestao de Alimentos e Bebidas (A&B)"
            }
        ],
        "certifications": [
            "Certificacao Oficial em Boas Praticas de Fabricacao (BPF) - SENAI / ANVISA",
            "Mestre em Fermentacao Natural e Viennoiserie - Institut Paul Bocuse / Formacao Executiva",
            "Curso Avancado de Controle Higienico-Sanitario dos Alimentos"
        ],
        "publications": [
            "RAMOS, M. O. Manual Pratico de Manutencao de Isca Viva (Levain) em Climas Tropicais. Revista Panificacao Brasileira, 2022."
        ],
        "languages": [
            {"language": "Portugues", "proficiency": "Nativo"},
            {"language": "Frances", "proficiency": "Intermediario Tecnico (B1)"},
            {"language": "Ingles", "proficiency": "Basico (A2)"}
        ]
    }

    bakery_job = {
        "title": "Chef Padeiro Encarregado de Produção Artesanal",
        "description": "Buscamos chef padeiro com ampla vivência em fermentação natural, BPF/ANVISA, controle de CMV e gestão de equipe em padaria de alto padrão."
    }

    res_bakery = builder.build_custom_industry_resume(
        bakery_candidate,
        bakery_job["title"],
        bakery_job["description"],
        "curriculo_matheus_ramos_panificacao_ats.pdf"
    )
    test_results.append(audit_and_evaluate(res_bakery, "FOOD_BAKERY_GASTRONOMY"))

    # =========================================================================
    # CASO 3: ENGENHARIA CIVIL (GERENCIAMENTO DE OBRAS & BIM)
    # =========================================================================
    logger.info(">>> TESTE 3: ENGENHARIA CIVIL (GERENCIAMENTO DE OBRAS) <<<")
    eng_candidate = {
        "full_name": "Engª. Beatriz Martins Duarte",
        "email": "beatriz.duarte@engenhariacivil.com.br",
        "phone": "+55 (11) 98765-1122",
        "location": "Sao Paulo, SP - Brasil",
        "summary": (
            "Engenheira Civil Senior (CREA-SP 506.912/D) com 11 anos de experiencia em gestao e execucao de obras verticais "
            "residenciais e comerciais de grande porte (+60.000m²). Especialista em planejamento fisico-financeiro, "
            "metodologia Lean Construction, modelagem BIM (Revit/Navisworks) e orcamentacao com base em SINAPI/TCPO. "
            "Forte historico de entregas rigorosamente dentro do prazo e orcamento, com padrao PBQP-H Nivel A e ISO 9001."
        ),
        "skills": [
            "CREA Ativo com ART", "Gerenciamento de Obras", "Planejamento e Orcamento (SINAPI / TCPO)",
            "Metodologia BIM (Revit / Navisworks)", "Normas Regulamentadoras (NR-18, NR-35)", "Lean Construction",
            "Controle Tecnologico do Concreto", "Sienge ERP", "MS Project e Primavera P6", "Gestao de Empreiteiros"
        ],
        "experiences": [
            {
                "role": "Engenheira Coordenadora Geral de Obras",
                "company": "Construtora Cyrela / Edificações",
                "period": "Mar 2020 - Presente",
                "highlights": [
                    "2 torres residenciais de alto padrao (42.000m²) | Custo final 4,8% abaixo do orcado | Zero acidentes graves em 280 mil horas-homem.",
                    "Implantou sistema Last Planner (Lean Construction) reduzindo o ciclo de execucao de lajes de 10 para 7 dias por pavimento.",
                    "Compatibilizou 100% dos projetos hidraulicos, eletricos e estruturais via plataforma BIM Navisworks, eliminando R$ 1,2M em retrabalho."
                ]
            },
            {
                "role": "Engenheira Residente de Campo",
                "company": "Tecnisa Engenharia",
                "period": "Ago 2015 - Fev 2020",
                "highlights": [
                    "Fiscalizou execucao estrutural e fundacoes profundas (helice continua) garantindo estrita adesao as normas ABNT.",
                    "Liderou auditorias de qualidade PBQP-H Nivel A e ISO 9001 sem nenhuma nao-conformidade critica apontada."
                ]
            }
        ],
        "education": [
            {
                "degree": "MBA em Gestao de Projetos e Obras Civis",
                "institution": "Escola Politecnica da USP (Poli-USP / PECE)",
                "period": "2018 - 2019",
                "details": "Enfase em Lean Construction e Gerenciamento de Custos"
            },
            {
                "degree": "Graduacao em Engenharia Civil (CREA-SP)",
                "institution": "Universidade Estadual de Campinas (UNICAMP)",
                "period": "2009 - 2014",
                "details": "Bolsista de Iniciacao Cientifica em Estruturas de Concreto Armado"
            }
        ],
        "certifications": [
            "CREA-SP com Acervo Tecnico (ARTs) de +60.000m² comprovados",
            "PMP (Project Management Professional) - PMI Institute (Ativo desde 2021)",
            "Certificacao Profissional Autodesk Revit & Navisworks",
            "Auditor Interno PBQP-H e ISO 9001"
        ],
        "publications": [
            "DUARTE, B. M. Aplicacao da Filosofia Lean Construction na Reducao de Prazos de Estruturas Verticais. Congresso Brasileiro de Engenharia, 2022."
        ],
        "languages": [
            {"language": "Portugues", "proficiency": "Nativo"},
            {"language": "Ingles", "proficiency": "Avancado (C1)"}
        ]
    }

    eng_job = {
        "title": "Engenheiro Civil Gerente de Obras Prediais",
        "description": "Buscamos Engenheiro Civil com CREA ativo, experiência em obras residenciais verticais de grande porte, domínio de Sienge, BIM e Lean Construction."
    }

    res_eng = builder.build_custom_industry_resume(
        eng_candidate,
        eng_job["title"],
        eng_job["description"],
        "curriculo_beatriz_duarte_engenharia_ats.pdf"
    )
    test_results.append(audit_and_evaluate(res_eng, "CIVIL_ENGINEERING_CONSTRUCTION"))

    # =========================================================================
    # COMPILAÇÃO DO RELATÓRIO CONSOLIDADO
    # =========================================================================
    summary_report = {
        "timestamp": datetime.now().isoformat(),
        "total_industries_tested": len(test_results),
        "results": test_results,
        "overall_status": "ALL_APPROVED" if all(r["ats_score"] == 100 for r in test_results) else "REVIEW"
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)

    logger.info("=== BATERIA MULTI-INDÚSTRIA FINALIZADA COM SUCESSO ===")
    return summary_report


def audit_and_evaluate(build_result: Dict[str, Any], expected_industry: str) -> Dict[str, Any]:
    pdf_path = build_result["pdf_path"]
    reader = pypdf.PdfReader(pdf_path)
    extracted_text = ""
    for p in reader.pages:
        extracted_text += p.extract_text() or ""

    # Validar seções canônicas
    canonical_sections = [
        "RESUMO PROFISSIONAL", "HABILIDADES E COMPETENCIAS", "EXPERIENCIA PROFISSIONAL",
        "FORMACAO ACADEMICA", "CERTIFICACOES E TITULOS"
    ]
    detected_sections = [s for s in canonical_sections if s in extracted_text.upper()]
    ats_score = 100 if len(detected_sections) == len(canonical_sections) else int((len(detected_sections)/len(canonical_sections))*100)

    # Validar presença de métricas com barras (|)
    has_metrics_bars = "|" in extracted_text

    return {
        "industry_key": expected_industry,
        "industry_display": build_result["industry_identified"],
        "pdf_filename": build_result["filename"],
        "pdf_path": pdf_path,
        "pages_count": len(reader.pages),
        "total_chars": len(extracted_text),
        "ats_score": ats_score,
        "all_sections_present": ats_score == 100,
        "metrics_bars_detected": has_metrics_bars,
        "status": "APPROVED" if ats_score == 100 else "FAIL"
    }


if __name__ == "__main__":
    report = run_multi_industry_tests()
    print("\n" + "=" * 70)
    print("RELATÓRIO CONSOLIDADO DE AUDITORIA MULTI-INDÚSTRIA (ATS 100%)")
    print("=" * 70)
    print(f"Status Geral: {report['overall_status']}")
    for r in report["results"]:
        print(f"\n[SETOR: {r['industry_display']}]")
        print(f"  - Arquivo: {r['pdf_filename']}")
        print(f"  - Paginas: {r['pages_count']} | Caracteres: {r['total_chars']}")
        print(f"  - Score ATS: {r['ats_score']}/100 ({r['status']})")
        print(f"  - Metricas com Barras (|): {'Sim' if r['metrics_bars_detected'] else 'Nao'}")
    print("=" * 70)
