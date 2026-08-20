import os
from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    # Remove BOM (U+FEFF) e espaços que o PowerShell pode injetar via CLI
    val = os.getenv(key, default)
    return val.lstrip("﻿").strip() if val else default


DISCORD_WEBHOOK_URL = _env("DISCORD_WEBHOOK_URL")
DISCORD_WEBHOOK_DESIGNER   = _env("DISCORD_WEBHOOK_DESIGNER")
DISCORD_WEBHOOK_DESIGNER_2 = _env("DISCORD_WEBHOOK_DESIGNER_2")
DISCORD_WEBHOOK_CXCS = _env("DISCORD_WEBHOOK_CXCS")
DISCORD_WEBHOOK_AUTOMACAO = _env("DISCORD_WEBHOOK_AUTOMACAO")
DISCORD_WEBHOOK_DEV   = _env("DISCORD_WEBHOOK_DEV")
DISCORD_WEBHOOK_EDFIS = _env("DISCORD_WEBHOOK_EDFIS")
DISCORD_WEBHOOK_CRM   = _env("DISCORD_WEBHOOK_CRM")
DISCORD_WEBHOOK_DATA  = _env("DISCORD_WEBHOOK_DATA")
DISCORD_WEBHOOK_POPM  = _env("DISCORD_WEBHOOK_POPM")
DISCORD_WEBHOOK_QA    = _env("DISCORD_WEBHOOK_QA")

# Upstash Redis (deduplicação — substitui SQLite no serverless)
UPSTASH_REDIS_REST_URL = _env("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = _env("UPSTASH_REDIS_REST_TOKEN")

# Fallback local: SQLite (usado quando não há Redis configurado)
DB_PATH = os.getenv("DB_PATH", "vagas.db")

# Palavras-chave por categoria — filtro aplicado no título + descrição
KEYWORDS = {
    "automacao_presencial": [
        # Cargos
        "engenheiro de automação", "engenheiro de automacao",
        "engenheiro de automação industrial", "engenheiro automação industrial",
        "engenheiro de controle e automação", "engenheiro de controle e automacao",
        "engenheiro eletricista", "engenheiro elétrico", "engenheiro eletrico",
        "engenheiro mecatrônico", "engenheiro mecatronico",
        "técnico de automação", "tecnico de automacao",
        "analista de automação", "analista de automacao",
        "analista de instrumentação", "analista de instrumentacao",
        "supervisor de automação", "supervisor de automacao",
        "especialista em automação", "especialista em automacao",
        # Tecnologias
        "programador clp", "programador plc",
        "desenvolvedor clp", "desenvolvedor plc",
        "automação industrial", "automacao industrial",
        "controle e automação", "controle e automacao",
        "instrumentação industrial", "instrumentacao industrial",
        "instrumentação e controle",
        "SCADA", "CLP", "PLC", "DCS", "HMI",
        "Siemens TIA Portal", "Allen Bradley", "Rockwell",
        "STEP 7", "WinCC", "FactoryTalk",
        "commissioning automação", "startup automação",
        "redes industriais", "fieldbus", "profibus", "profinet",
        "IEC 61131",
    ],
    "automacao_remote": [
        # Cargos
        "projetista de automação", "projetista de automacao",
        "projetista elétrico", "projetista eletrico",
        "projetista de painéis", "projetista de paineis",
        "projetista industrial",
        "projetista mecânico", "projetista mecanico",
        "projetista hidráulico", "projetista hidraulico",
        "projetista CAD",
        "projetista de sistemas elétricos",
        "projetista sênior", "projetista pleno", "projetista junior",
        "engenheiro projetista",
        "analista projetista",
        # Ferramentas / disciplinas
        "EPLAN", "AutoCAD Electrical",
        "projetos elétricos industriais", "projetos de automação",
        "dimensionamento elétrico",
        "quadros elétricos", "painéis elétricos", "paineis eletricos",
        "diagramas elétricos", "diagramas unifilares",
        "SolidWorks Electrical",
        "memorial descritivo elétrico",
        "lista de materiais elétricos",
    ],
    "crm": [
        "crm",
        "analista de crm", "analista crm",
        "especialista de crm", "especialista em crm", "especialista crm",
        "coordenador de crm", "coordenador crm",
        "gerente de crm", "gerente crm",
        "gestor de crm", "gestor crm",
        "diretor de crm", "diretor crm",
        "head de crm", "head crm", "head of crm",
        "supervisor de crm", "supervisor crm",
        "consultor de crm", "consultor crm",
        "assistente de crm", "assistente crm",
        "aprendiz crm", "estagiario crm", "estagiário crm",
        "crm analyst", "crm manager", "crm specialist",
        "crm coordinator", "crm strategist", "crm director",
        "crm marketing", "marketing de crm",
        "marketing de relacionamento",
        "analista de relacionamento crm",
        "jornada do cliente", "jornadas de clientes",
        "automacao de crm", "automação de crm",
        "canais digitais crm", "canais de relacionamento",
        "analytics crm", "crm analytics", "dados de crm",
        "analista de campanhas crm",
        "lifecycle marketing crm",
        "growth crm", "crm growth",
        "implementacao crm", "implementação crm",
        "analista funcional crm", "consultor funcional crm",
        "crm implementation", "crm developer",
        "desenvolvedor crm", "engenheiro crm",
        "salesforce",
        "salesforce administrator", "salesforce admin",
        "salesforce developer", "salesforce consultant",
        "salesforce business analyst", "salesforce architect",
        "analista salesforce", "analista de salesforce",
        "consultor salesforce", "desenvolvedor salesforce",
        "estagiario salesforce", "assistente salesforce",
        "marketing cloud", "sales cloud", "service cloud",
        "salesforce marketing cloud", "salesforce cpq",
        "salesforce data cloud", "agentforce",
        "hubspot",
        "analista de hubspot", "analista hubspot",
        "especialista hubspot", "consultor hubspot",
        "hubspot administrator", "hubspot developer",
        "rd station",
        "analista de rd station", "especialista rd station",
        "consultor rd station",
        "dynamics crm", "microsoft dynamics crm",
        "pipedrive", "zoho crm",
        "activecampaign", "active campaign",
        "braze", "insider crm", "dinamize",
        "klaviyo", "oracle responsys",
        "loyalty crm", "fidelização crm",
        "retencao de clientes crm", "retenção de clientes crm",
        "segmentacao crm", "segmentação crm",
        "personalizacao crm", "personalização crm",
        "martech crm", "cdp crm",
    ],
    "data": [
        # Analista de dados
        "analista de dados", "analista dados", "data analyst",
        "analista de analytics", "analytics analyst",
        # Business Intelligence
        "analista de business intelligence", "analista de bi", "analista bi",
        "business intelligence analyst", "bi analyst",
        "analista power bi", "especialista power bi",
        "analista tableau", "especialista tableau",
        "power bi developer", "power bi engineer",
        # Cientista de dados
        "cientista de dados", "data scientist",
        "ciência de dados", "ciencia de dados",
        # Engenheiro de dados
        "engenheiro de dados", "engenheira de dados",
        "data engineer", "analytics engineer",
        "engenharia de dados",
        # Arquitetura / liderança de dados
        "arquiteto de dados", "arquiteta de dados", "data architect",
        "head de dados", "head of data", "gerente de dados",
        "líder de dados", "lider de dados",
        # Machine Learning / IA
        "machine learning engineer", "ml engineer",
        "engenheiro de machine learning", "engenheiro de ml",
        "ai engineer", "engenheiro de ia", "engenheiro de inteligência artificial",
        "mlops",
        # Ferramentas como cargo
        "analista dbt", "especialista dbt",
        "analista databricks", "engenheiro databricks",
        "analista snowflake",
        # Dados em geral
        "profissional de dados", "especialista em dados",
        "data steward", "data governance",
        "analista de dados jr", "analista de dados pleno", "analista de dados senior",
    ],
    "edfis": [
        # Cargo principal
        "educação física", "educacao fisica",
        "ed. física", "ed fisica",
        # Personal e Fitness
        "personal trainer",
        "instrutor de academia", "instrutor fitness",
        "instrutor de musculação", "instrutor de musculacao",
        "professor de musculação", "professor de musculacao",
        "treinador de musculação", "treinador de musculacao",
        # Preparação física
        "preparador físico", "preparador fisico",
        "preparação física", "preparacao fisica",
        # Modalidades
        "professor de natação", "professor de natacao",
        "instrutor de natação", "instrutor de natacao",
        "professor de pilates", "instrutor de pilates",
        "professor de yoga", "instrutor de yoga",
        "professor de crossfit", "instrutor de crossfit",
        "professor de dança", "professor de danca",
        "professor de artes marciais",
        "professor de futebol", "professor de volei", "professor de vôlei",
        # Coordenação / gestão esportiva
        "coordenador esportivo", "coordenador de esportes",
        "gestor esportivo", "supervisor esportivo",
        "professor de esportes",
        # Saúde corporativa / bem-estar
        "coordenador de bem-estar", "coordenador de wellness",
        "analista de saúde", "consultor de saúde",
    ],
    "po_pm": [
        # Product Owner
        "product owner", "po agile", "product owner jr", "product owner pleno",
        "product owner senior", "product owner sênior",
        "dono do produto", "dono de produto",
        # Product Manager
        "product manager", "gerente de produto", "gestora de produto",
        "gestor de produto", "gerente de produtos",
        "head of product", "head de produto", "head de produtos",
        "diretor de produto", "diretora de produto",
        "coordenador de produto", "coordenadora de produto",
        "líder de produto", "lider de produto",
        "product lead", "group product manager",
        # Product em geral (cargos com "produto" no título)
        "analista de produto", "analista de produtos",
        "especialista de produto", "especialista em produto",
        # Inglês
        "chief product officer", "cpo",
        "vp of product", "vp product",
        "senior product manager", "junior product manager",
        "associate product manager", "apm",
    ],
    "qa": [
        # QA em PT
        "analista de qualidade", "analista de testes", "analista de teste",
        "analista de qa", "analista qa",
        "engenheiro de qualidade", "engenheira de qualidade",
        "engenheiro de testes", "engenheira de testes",
        "especialista em qualidade", "especialista de qualidade",
        "especialista em testes", "especialista de testes",
        "coordenador de qualidade", "coordenadora de qualidade",
        "gerente de qualidade",
        "testador", "testadora",
        # QA em EN
        "quality analyst", "quality assurance", "quality engineer",
        "qa analyst", "qa engineer", "qa specialist", "qa lead",
        "qa manager", "qa automation", "qa manual",
        "test analyst", "test engineer", "test lead", "test manager",
        "tester", "software tester",
        # Automação de testes
        "automation tester", "automation qa",
        "sdet",
        "engenheiro de automação de testes",
        # Combinações comuns em BR
        "analista de testes funcionais", "analista de testes manuais",
        "analista de testes automatizados", "analista de automação de testes",
    ],
    "dev": [
        # Cargos PT
        "desenvolvedor", "desenvolvedora",
        "programador", "programadora",
        "engenheiro de software", "engenheira de software",
        # Cargos EN
        "developer", "software engineer", "software developer",
        # Especialidades
        "frontend", "front-end", "front end",
        "backend", "back-end", "back end",
        "fullstack", "full-stack", "full stack",
        "devops", "dev ops",
        "mobile developer", "web developer",
        "tech lead", "technical lead",
        # Liderança técnica e gestão de TI
        "gerente de tecnologia", "gerente de ti", "gerente de engenharia",
        "gerente de desenvolvimento", "gerente de software",
        "head de tecnologia", "head de ti", "head de engenharia",
        "head of engineering", "head of technology",
        "diretor de tecnologia", "diretor de ti", "diretor de engenharia",
        "diretor de desenvolvimento",
        "vp de engenharia", "vp de tecnologia",
        "vp of engineering", "vp engineering",
        "cto", "chief technology officer", "chief technical officer",
        "engineering manager", "engenheiro manager",
        "líder técnico", "lider tecnico",
        "líder de engenharia", "lider de engenharia",
        "coordenador de desenvolvimento", "coordenador de tecnologia",
        "coordenador de ti",
        # Linguagens/stacks como título (comum em job boards de TI)
        "flutter developer", "react developer", "node developer",
        "python developer", "java developer", "php developer",
    ],
    "designer": [
        # Cargos
        "designer", "designer gráfico", "designer grafico", "product designer",
        "ux designer", "ui designer", "web designer", "motion designer",
        "graphic designer", "visual designer", "design de produto",
        "designer de produto", "design gráfico", "design grafico",
        # Disciplinas / ferramentas
        "ux", "ui", "user experience", "user interface", "figma",
        "ilustração", "ilustracao", "illustrator", "branding",
        "identidade visual", "motion", "motion design", "visual design",
        "design system", "web design", "webdesign", "arte", "photoshop",
        "indesign", "prototipagem", "wireframe", "usabilidade",
        "acessibilidade", "accessibility", "criativo", "criativa",
        "ux/ui", "ui/ux",
    ],
    "cxcs": [
        # Cargos principais
        "customer success", "customer success manager", "csm",
        "sucesso do cliente", "sucesso de cliente",
        "cs jr", "cs pleno", "cs sr", "cs senior", "cs junior",
        "customer experience", "cx",
        "experiência do cliente", "experiencia do cliente",
        # Atendimento / suporte
        "atendimento ao cliente", "suporte ao cliente", "sac",
        "analista de atendimento", "assistente de atendimento",
        "analista de suporte", "assistente de suporte",
        "customer support", "support analyst",
        # Relacionamento
        "relacionamento com cliente", "relacionamento com o cliente",
        "analista de relacionamento", "gestão de relacionamento",
        "account manager", "key account",
        # Ciclo de vida
        "onboarding", "churn", "retenção", "retencao",
        "upsell", "cross-sell", "implementação", "implementacao",
        # Métricas / ferramentas
        "nps", "csat", "customer health", "customer journey",
        "voz do cliente", "voice of customer",
        # Help desk
        "help desk", "helpdesk", "service desk",
    ],
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_TIMEOUT = 8
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0"))  # 0 em serverless
