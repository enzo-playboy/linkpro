"""
Gerador de Currículo Financeiro Turbinado V2 (Asset Manager / Portfolio Manager)
JobAutomator AI - Incorpora 100% dos requisitos de ATS de elite do Claude.
"""

import os
import json
from pdf_generator import ResumePDFGenerator
import pypdf

def generate_finance_resume_v2():
    finance_data = {
        "full_name": "Rodrigo Siqueira Bueno, CFA Charterholder, CGA",
        "email": "rodrigo.bueno@capitalpartners.com.br",
        "phone": "+55 (11) 98111-2233",
        "location": "Sao Paulo, SP - Brasil",
        "linkedin": "linkedin.com/in/rodrigo-bueno-cfa",
        "summary": (
            "Senior Portfolio Manager e Asset Allocator (CFA Charterholder titular / CGA ANBIMA) com 10 anos de experiencia comprovada "
            "na gestao discricionaria de fundos multimercado macro e renda variavel. Especialista em modelagem quantitativa, "
            "valuation DCF, analise fundamentalista e gestao de risco (VaR, Sortino e Sharpe). Liderou equipes multidisciplinares "
            "de analistas, reportando diretamente ao Board e C-Level, com historico consistente de geracao de alpha e conformidade "
            "estrita perante normativas da CVM, BACEN e ANBIMA."
        ),
        "skills": {
            "Valuation & Modelagem": [
                "Valuation DCF", "WACC", "FCD", "Analise de Sensibilidade", "LBO", "M&A", "Modelagem de Cenarios"
            ],
            "Analise Quantitativa & Risco": [
                "VaR (Value at Risk)", "CVaR", "Indice Sharpe", "Sortino Ratio", "Maximo Drawdown",
                "Modelos GARCH", "Stress Testing", "Backtesting Sistematico", "Regressao Multipla"
            ],
            "Alocacao de Ativos & Mercado": [
                "Modern Portfolio Theory (MPT)", "Rebalanceamento Tatico", "Asset-Liability Management (ALM)",
                "Renda Fixa e Variavel", "Derivativos e Hedge Cambial", "Mercado de Capitais"
            ],
            "Programacao & Plataformas": [
                "Python (Pandas, NumPy, Scikit-learn)", "VBA Avancado", "SQL", "APIs Bloomberg Terminal",
                "Refinitiv Eikon", "Economatica", "Power BI", "Tableau"
            ],
            "Lideranca & Soft Skills": [
                "Gestao de Equipes Multidisciplinares (8+ analistas)", "Comunicacao Executiva com Board e C-Level",
                "Apresentacoes a Investidores Institucionais", "Negociacao com Custodiantes e Prime Brokers",
                "Mentoria e Desenvolvimento de Analistas"
            ]
        },
        "experiences": [
            {
                "role": "Lead Portfolio Manager (Fundos Multimercado)",
                "company": "Vinci Capital Partners",
                "period": "Jan 2021 - Presente",
                "highlights": [
                    "AUM sob gestao direta: R$ 580M | Retorno acumulado: 124% do CDI | Indice Sharpe: 1.48 | Reducao de Drawdown Maximo em 32%.",
                    "Liderou comite semanal de investimentos com 1.200+ cotistas institucionais e private, gerando relatorios de alocacao com 99%+ de compliance regulatorio (CVM/ANBIMA) e reduzindo o tempo de fechamento operacional em 40%.",
                    "Estruturou estrategias sistematicas de hedge cambial e derivativos de juros, preservando R$ 45M em capital durante choques de volatilidade macroeconomica.",
                    "Coordenou equipe de 8 analistas de research e risco, estabelecendo trilhas de mentoria e rotinas de backtesting sistematico de estrategias."
                ]
            },
            {
                "role": "Analista Senior de Equity Research & Risco Quantitativo",
                "company": "Itaú BBA / Asset Management",
                "period": "Mar 2016 - Dez 2020",
                "highlights": [
                    "Desenvolveu pipeline automatizado em Python integrado a API Bloomberg para analise de demonstracoes financeiras: reduziu tempo de analise de 6 horas por dia para 30 minutos por dia (92% de ganho de eficiencia operacional) com precisao 15% superior ao modelo anterior, cobrindo 18 ativos sob analise.",
                    "Liderou cobertura de 18 empresas do setor de commodities e varejo, emitindo relatorios de recomendacao com taxa de acerto de recomendacao de 74% em 3 anos.",
                    "Conduziu reunioes de due diligence e apresentacoes executivas para diretores de RI e gestores de fundos parceiros."
                ]
            }
        ],
        "education": [
            {
                "degree": "Mestrado Profissional em Economia e Financas",
                "institution": "Fundacao Getulio Vargas (FGV-EESP)",
                "period": "2018 - 2020",
                "details": "Dissertacao aprovada com louvor em Otimizacao de Carteiras com Assimetria de Volatilidade"
            },
            {
                "degree": "Bacharelado em Engenharia de Producao",
                "institution": "Escola Politecnica da Universidade de Sao Paulo (Poli-USP)",
                "period": "2011 - 2015",
                "details": "Enfase em Modelagem Financeira, Pesquisa Operacional e Estatistica"
            }
        ],
        "certifications": [
            "CFA Charterholder (Chartered Financial Analyst) - CFA Institute | Membro Efetivo Regular desde 2019 (Charterholder No. 289410 - Foco em Gestao de Portfolio e Etica)",
            "CGA (Certificacao de Gestores ANBIMA) - ANBIMA | Ativo desde 2020 | Renovacao Vigente",
            "CNPI (Certificado Nacional do Profissional de Investimento) - APIMEC | Ativo",
            "ANBIMA CEA (Certificacao de Especialista em Investimentos) | Ativo"
        ],
        "publications": [
            "BUENO, R. S. (2021). Impacto da Assimetria de Volatilidade na Otimizacao de Portfolios Brasileiros. Revista Brasileira de Financas, Vol. 19, No. 4, pp. 45-67. (Citacoes: 14+ | Adotado na politica de 2 fundos multimercado | DOI: 10.1590/rbf.2021.04).",
            "Apresentacao em Congresso: Machine Learning aplicado a Alocacao Dinamica de Ativos - ANBIMA Nordeste, 2022.",
            "Apresentacao em Congresso: Gestao Quantitativa de Risco em Mercados Emergentes - APIMEC Sudeste, 2021."
        ],
        "languages": [
            {"language": "Portugues", "proficiency": "Nativo"},
            {"language": "Ingles", "proficiency": "Fluente / Negociacoes Internacionais (C2 - TOEFL 115)"},
            {"language": "Espanhol", "proficiency": "Avancado (B2)"}
        ]
    }

    generator = ResumePDFGenerator(output_dir="generated_resumes")
    filename = "curriculo_rodrigo_bueno_finance_v2_ats.pdf"
    pdf_path = generator.generate_pdf(finance_data, filename)

    print("=" * 65)
    print(f"PDF Financeiro V2 Gerado com Sucesso: {pdf_path}")
    print("=" * 65)

    reader = pypdf.PdfReader(pdf_path)
    print(f"Total de Paginas: {len(reader.pages)}")
    extracted_text = ""
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        extracted_text += text
        print(f"\n--- PAGINA {idx + 1} ({len(text)} caracteres) ---")
        print(text[:350] + "...\n")

    print("Auditoria das Secoes Detectadas pelo ATS:")
    sections = [
        "RESUMO PROFISSIONAL",
        "HABILIDADES E COMPETENCIAS",
        "EXPERIENCIA PROFISSIONAL",
        "FORMACAO ACADEMICA",
        "CERTIFICACOES E TITULOS",
        "PUBLICACOES E PESQUISAS",
        "IDIOMAS"
    ]
    for section in sections:
        found = section in extracted_text.upper()
        print(f"  [{'OK' if found else 'FAIL'}] {section}")

    return pdf_path

if __name__ == "__main__":
    generate_finance_resume_v2()
