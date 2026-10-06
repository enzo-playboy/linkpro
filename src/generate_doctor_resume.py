"""
Gerador de Currículo Médico Turbinado para ATS (V2 - Com todas as recomendações)
JobAutomator AI - Especialidade: Cardiologia / Terapia Intensiva / Clínica Médica
"""

import os
import json
from pdf_generator import ResumePDFGenerator
import pypdf

def generate_doctor_resume_v2():
    doctor_data = {
        "full_name": "Dra. Camila Barbosa Alencar",
        "email": "dra.camila.alencar@medicina.usp.br",
        "phone": "+55 (11) 98456-7890",
        "location": "Sao Paulo, SP - Brasil",
        "summary": (
            "Medica Cardiologista e Intensivista (CRM-SP 189.432 | RQE 84.102 / 79.540) com 8 anos de experiencia em "
            "atendimento hospitalar de alta complexidade, Unidade Coronariana (UCO), Terapia Intensiva e Pronto Atendimento. "
            "Especialista no manejo clinico e intervencionista de sindromes coronarianas agudas, arritmias graves, insuficiencia "
            "cardiaca descompensada e choque circulatorio. Experiencia comprovada em lideranca de equipes multidisciplinares, "
            "implantacao de protocolos institucionais de dor toracica e auditoria assistencial baseada em diretrizes da SBC e AHA."
        ),
        "skills": [
            "Cardiologia Clinica", "Terapia Intensiva (UTI e UCO)", "Cateterismo Cardiaco (Indicacao e Pos-Operatorio)",
            "Ecocardiografia e POCUS Cardiotoracico", "Eletrofisiologia e Eletrocardiografia Avancada (ECG)",
            "ACLS e BLS (Suporte Avancado e Basico de Vida)", "Manejo de Via Aerea Dificil e IOT",
            "Ventilacao Mecanica Invasiva e Nao-Invasiva", "Acesso Venoso Central e Linha Arterial (PAI)",
            "Protocolo Institucional de Dor Toracica (SBC)", "Choque Cardiogenico e Suporte com BIA/Inotropicos",
            "Documentacao Clinica e Prontuario Eletronico (MV Soul, Tasy, Epimed)", "Medicina Baseada em Evidencias",
            "Lideranca Clinica e Comunicacao com Familiares", "Regulacao Medica (CROSS)"
        ],
        "experiences": [
            {
                "role": "Medica Rotineira / Diarista da Unidade Coronariana (UCO)",
                "company": "Hospital Israelita Albert Einstein",
                "period": "Jan 2022 - Presente",
                "highlights": [
                    "16 leitos criticos gerenciados | Sobrevida: 94,8% em IAM com/sem supra | Desospitalizacao segura acelerada em 18%.",
                    "Reduziu tempo porta-ECG em 50% (de 14 para 7 min) e alcancou tempo porta-balao medio de 52 min atraves da reestruturacao do protocolo integrado de dor toracica.",
                    "Coordenou visitas multidisciplinares diarias e auditoria de qualidade clinica, reduzindo taxa de readmissao em 30 dias para 6,2%.",
                    "Preceptora de 12 residentes medicos de Cardiologia e Terapia Intensiva com enfase em monitorizacao hemodinamica e choque."
                ]
            },
            {
                "role": "Medica Plantonista de Emergencia e UTI Cardiovascular",
                "company": "Instituto do Coracao (InCor - HCFMUSP)",
                "period": "Mar 2018 - Dez 2021",
                "highlights": [
                    "4.500+ atendimentos cardiovasculares de urgencia | Taxa de complicacao em procedimentos invasivos: <1%.",
                    "Conduziu cardioversoes sincronizadas, paracentese, drenagem de torax e punoes ecoguiadas em situacoes de instabilidade hemodinamica.",
                    "Manejou choque cardiogenico refratario com indicacao precisa e assistencia a Balão Intra-Aortico (BIA) e suporte inotropico avancado.",
                    "Membro ativo da Comissao de Revisao de Prontuarios e elaboracao de condutas clinicas baseadas nas diretrizes da SBC/ACC."
                ]
            },
            {
                "role": "Medica Clinica Geral / Reguladora Plantonista",
                "company": "Unidade de Pronto Atendimento (UPA) Central",
                "period": "Fev 2016 - Fev 2018",
                "highlights": [
                    "50+ pacientes atendidos por plantao de 12h sob classificacao de risco pelo Protocolo de Manchester.",
                    "Regulou mais de 800 transferencias hospitalares prioritarias de IAM e AVC via sistema CROSS com adesao estrita a tempos de resposta criticos."
                ]
            }
        ],
        "education": [
            {
                "degree": "Residencia Medica em Cardiologia (RQE 84.102)",
                "institution": "Instituto do Coracao (InCor - HCFMUSP)",
                "period": "2018 - 2020",
                "details": "Titulo e credenciamento oficial pelo MEC e Sociedade Brasileira de Cardiologia"
            },
            {
                "degree": "Residencia Medica em Clinica Medica (RQE 79.540)",
                "institution": "Hospital das Clinicas da Faculdade de Medicina da USP (HCFMUSP)",
                "period": "2016 - 2018",
                "details": "Treinamento avancado em enfermaria, UTI e departamento de emergencia"
            },
            {
                "degree": "Graduacao em Medicina (CRM-SP 189.432)",
                "institution": "Faculdade de Medicina da Universidade de Sao Paulo (FMUSP)",
                "period": "2010 - 2015",
                "details": "Internato em centros de referencia terciarios e quaternarios"
            }
        ],
        "certifications": [
            "Titulo de Especialista em Cardiologia (TEC) - Sociedade Brasileira de Cardiologia (SBC/AMB) - Emitido 2020",
            "ACLS (Advanced Cardiovascular Life Support) - American Heart Association (AHA) - Certificacao Ativa (2020 - Presente)",
            "BLS (Basic Life Support) - American Heart Association (AHA) - Certificacao Ativa",
            "FCCS (Fundamental Critical Care Support) - Society of Critical Care Medicine (SCCM) - Certificacao 2021",
            "POCUS Cardiotoracico - Ecografia Point-of-Care em Urgencia e Terapia Intensiva (2022)"
        ],
        "publications": [
            "ALENCAR, C. B. et al. Otimizacao do tempo porta-balao em sindromes coronarianas agudas atraves de protocolos multidisciplinares integrados. Arquivos Brasileiros de Cardiologia (ABC Cardiol), 2023.",
            "ALENCAR, C. B.; SILVA, M. R. Manejo hemodinamico e desfechos clinicos em choque cardiogenico refratario com suporte por BIA: serie de 120 casos. Congresso da Sociedade Brasileira de Cardiologia (SBC), 2021."
        ],
        "languages": [
            {"language": "Portugues", "proficiency": "Nativo"},
            {"language": "Ingles", "proficiency": "Fluente / Tecnico Medico (C2)"},
            {"language": "Espanhol", "proficiency": "Intermediario (B2)"}
        ]
    }

    generator = ResumePDFGenerator(output_dir="generated_resumes")
    filename = "curriculo_medico_dra_camila_alencar_v2_ats.pdf"
    pdf_path = generator.generate_pdf(doctor_data, filename)

    print("=" * 65)
    print(f"PDF Medico V2 Gerado com Sucesso: {pdf_path}")
    print("=" * 65)

    # Auditar leitura via pypdf
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
    generate_doctor_resume_v2()
