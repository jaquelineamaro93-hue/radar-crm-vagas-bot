import os
from dotenv import load_dotenv

load_dotenv()

def _env(key: str, default: str = "") -> str:
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

UPSTASH_REDIS_REST_URL = _env("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = _env("UPSTASH_REDIS_REST_TOKEN")

DB_PATH = os.getenv("DB_PATH", "vagas.db")

KEYWORDS = {
    "crm": [
        "crm copywriter", "lifecycle copywriter", "redator de ciclo de vida", "growth copywriter", "growth writer", "forward deployed engineer", "fde ai martech", "ai agent architect", "ai agent product manager", "ai solutions architect crm", "desenvolvedor de agentes de ia", "engenheiro de integracao de agentes", "especialista em crm e inteligencia artificial", "ai lifecycle marketing", "crm preditivo", "predictive crm specialist", "ai-driven growth specialist", "analista de dados de crm machine learning", "real-time personalization specialist", "ia conversacional", "conversational ai specialist", "prompt engineer crm", "prompt engineer cx", "conversational ai product owner", "automacao de atendimento ia generativa", "arquiteto de bots agentes autonomos", "ai martech operations specialist", "cdp ai data specialist", "orquestracao de agentes crm", "engenheiro de dados de consumidor ia", "head of ai customer experience", "head of ai-driven crm", "tech lead agentes de ia", "gerente de agentes de ia", "lifecycle marketing specialist", "lifecycle marketing manager", "retention marketing specialist", "retention marketing manager", "especialista em engajamento e reativacao", "especialista de prevencao a churn", "churn specialist", "customer marketing specialist", "customer marketing manager", "monetizacao de base", "marketing automation specialist", "marketing automation architect", "especialista de martech", "analista de martech", "marketing operations analyst", "marketing operations manager", "marketing ops", "arquiteto de solucoes de marketing", "growth marketing manager", "growth marketing specialist", "retention growth manager", "ltv specialist", "ltv manager", "product growth analyst", "especialista em canais proprietarios", "owned media specialist", "inbound marketing specialist", "inbound marketing manager", "messaging push notification specialist", "email marketing manager", "analista de mensageria whatsapp", "loyalty specialist", "loyalty manager", "especialista em programas de fidelidade", "gerente de programas de fidelidade", "customer journey specialist", "customer journey manager", "especialista de mapeamento de jornada", "customer experience specialist", "customer experience manager", "analista de voc voice of customer", "analista de nps", "cdp specialist", "customer data platform specialist", "customer data analyst", "customer intelligence specialist", "database marketing analyst", "analista de segmentacao consumidor", "martech data specialist", "product manager martech", "product manager lifecycle", "product manager growth", "product owner plataformas de marketing", "analista de crm marketing", "analista de marketing de relacionamento", "analista de regua de relacionamento", "analista de automacao de marketing", "analista de inbound marketing", "analista de lifecycle marketing", "analista de retencao e engajamento", "growth crm specialist", "retention specialist", "especialista em crm e ltv", "analista de crm data analytics", "analista de operacoes de crm", "crm ops", "especialista de growth e lifecycle", "engenharia de ia agentes fde", "forward deployed engineer ai martech cx", "forward deployed ai agent engineer", "ai agent architect desenvolvedor de agentes de ia", "ai solutions architect crm cx automation", "ai agent product manager pm de agentes de ia", "engenheiro de integracao de agentes de ia crm", "crm growth lifecycle potencializados por ia", "especialista em crm inteligencia artificial", "ai lifecycle marketing manager specialist", "especialista em crm preditivo predictive crm", "ai driven growth specialist", "analista de dados crm machine learning", "especialista em personalizacao em tempo real", "ia conversacional mensageria engenharia prompt", "engenheiro especialista ia conversacional whatsapp", "prompt engineer jornadas cx crm vendas", "conversational ai product owner specialist", "analista automacao atendimento ia generativa", "arquiteto bots agentes autonomos relacionamento", "ai martech operations specialist marketing ops", "cdp ai data specialist", "especialista orquestracao agentes fluxos crm", "engenheiro dados consumidor modelos ia", "head ai customer experience cx", "head ai driven crm growth", "tech lead lideranca tecnica agentes ia martech", "gerente agentes ia inovacao crm", "lifecycle marketing specialist manager", "retention marketing specialist", "especialista engajamento reativacao", "especialista prevencao churn retencao clientes", "customer marketing specialist manager", "especialista monetizacao base upsell cross sell", "marketing automation specialist architect", "especialista analista martech", "marketing operations analyst manager ops", "especialista ferramentas marketing salesforce hubspot", "arquiteto solucoes marketing", "especialista fluxos vendas nutricao", "growth marketing manager specialist base", "retention growth manager", "ltv specialist manager", "product growth analyst onboarding ativacao retencao", "especialista canais proprietarios owned media", "inbound marketing specialist manager", "messaging push notification specialist", "email marketing manager copywriter conversao base", "analista especialista mensageria whatsapp sms", "loyalty specialist manager", "gerente especialista programas fidelidade recompensas", "especialista parcerias beneficios perks loyalty", "community manager especialista comunidades clientes", "customer journey specialist manager", "especialista mapeamento jornada cliente", "customer experience specialist manager cx", "analista voc voice customer nps", "customer success manager csm onboarding retencao", "cdp specialist customer data platform", "customer data analyst intelligence specialist", "database marketing analyst", "analista segmentacao comportamento consumidor", "martech data specialist", "product manager pm martech lifecycle growth", "product owner po plataformas marketing canais", "especialista solucoes cx martech", "analista crm jr pl sr", "analista crm marketing", "analista marketing relacionamento", "analista regua relacionamento", "analista automacao marketing", "analista inbound marketing email", "analista lifecycle marketing ciclo vida", "analista retencao engajamento", "growth crm specialist especialista growth", "analista especialista retencao", "especialista crm ltv", "especialista crm martech", "analista crm data analytics", "analista operacoes crm ops", "especialista growth lifecycle", "analista especialista canais digitais", "especialista crm canais push whatsapp sms", "analista especialista programas fidelidade", "especialista customer experience crm cx", "analista omnichannel crm", "coordenador crm", "coordenador crm growth", "coordenador lifecycle marketing", "coordenador marketing relacionamento fidelidade", "gerente crm", "gerente crm martech", "gerente crm cx fidelizacao", "gerente lifecycle retention", "head crm", "head crm growth", "head customer marketing retention", "head lifecycle martech", "diretor crm customer experience", "vp chief customer officer cco", "crm copywriter", "lifecycle copywriter", "redator ciclo vida", "growth copywriter", "growth writer", "copywriter inbound automacao", "copywriter mensageria conversao", "copywriter whatsapp push sms", "copywriter revops", "copywriter sales enablement", "conversational copywriter", "redator agentes ia bots", "email marketing copywriter", "ux writer microcopy", "ux writer jornadas", "ux writer reguas", "crm designer", "lifecycle designer", "designer relacionamento", "growth designer", "designer automacao marketing", "email marketing designer", "designer html css email", "designer canais proprietarios", "designer owned media", "designer whatsapp push in app", "visual designer retencao", "visual designer ltv", "martech visual specialist", "designer braze insider", "ui designer jornadas clientes", "designer ciclo vida", "designer growth retencao", "designer plataformas automacao", "designer rd station braze insider", "designer programas fidelidade", "creative growth specialist", "especialista criacao growth", "conversational experience designer", "especialista conteudo hubspot rd station", "braze content specialist", "insider content specialist", "revops creative specialist", "creative operations specialist martech", "especialista criacao design regua relacionamento", "especialista operacoes criativas martech",
,
        "crm copywriter",
        "lifecycle copywriter",
        "redator de ciclo de vida",
        "growth copywriter",
        "growth writer",
        "copywriter de inbound",
        "copywriter whatsapp push sms",
        "copywriter revops",
        "conversational copywriter",
        "redator para agentes de ia",
        "email marketing copywriter",
        "ux writer microcopy",
        "ux writer jornadas",
        "crm designer",
        "lifecycle designer",
        "designer de relacionamento",
        "growth designer",
        "email marketing designer",
        "designer html css email",
        "designer de canais proprietarios",
        "visual designer retencao",
        "martech visual specialist",
        "designer braze insider",
        "forward deployed engineer",
        "ai agent architect",
        "desenvolvedor de agentes de ia",
        "ai solutions architect crm",
        "ai agent product manager",
        "engenheiro de integracao agentes ia",
        "crm lifecycle ia",
        "ai lifecycle marketing manager",
        "crm preditivo",
        "ai-driven growth specialist",
        "ia conversacional whatsapp",
        "prompt engineer crm vendas",
        "conversational ai product owner",
        "automacao atendimento ia",
        "arquiteto de bots agentes autonomos",
        "ai martech operations",
        "cdp ai data specialist",
        "especialista orquestracao agentes crm",
        "engenheiro dados consumidor ia",
        "head ai customer experience",
        "head ai-driven crm growth",
        "tech lead agentes ia martech",
        "gerente agentes ia inovacao crm",
    ]
}
