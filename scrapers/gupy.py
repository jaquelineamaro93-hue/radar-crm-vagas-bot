"""
Scraper para Gupy — focado em CRM e áreas correlatas.
API: employability-portal.gupy.io/api/v1/jobs
"""
import requests
from .base import classify

SOURCE = "Gupy"
API_URL = "https://employability-portal.gupy.io/api/v1/jobs"


def scrape() -> list[dict]:
    vagas = []
    seen_urls: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
    })

    searches = [
        "forward deployed engineer",
        "fde ai martech",
        "ai agent architect",
        "ai agent product manager",
        "ai solutions architect crm",
        "desenvolvedor de agentes de ia",
        "engenheiro de integracao de agentes",
        "especialista em crm e inteligencia artificial",
        "ai lifecycle marketing",
        "crm preditivo",
        "predictive crm specialist",
        "ai-driven growth specialist",
        "analista de dados de crm machine learning",
        "real-time personalization specialist",
        "ia conversacional",
        "conversational ai specialist",
        "prompt engineer crm",
        "prompt engineer cx",
        "conversational ai product owner",
        "automacao de atendimento ia generativa",
        "arquiteto de bots agentes autonomos",
        "ai martech operations specialist",
        "cdp ai data specialist",
        "orquestracao de agentes crm",
        "engenheiro de dados de consumidor ia",
        "head of ai customer experience",
        "head of ai-driven crm",
        "tech lead agentes de ia",
        "gerente de agentes de ia",
        "lifecycle marketing specialist",
        "lifecycle marketing manager",
        "retention marketing specialist",
        "retention marketing manager",
        "especialista em engajamento e reativacao",
        "especialista de prevencao a churn",
        "churn specialist",
        "customer marketing specialist",
        "customer marketing manager",
        "monetizacao de base",
        "marketing automation specialist",
        "marketing automation architect",
        "especialista de martech",
        "analista de martech",
        "marketing operations analyst",
        "marketing operations manager",
        "marketing ops",
        "arquiteto de solucoes de marketing",
        "growth marketing manager",
        "growth marketing specialist",
        "retention growth manager",
        "ltv specialist",
        "ltv manager",
        "product growth analyst",
        "especialista em canais proprietarios",
        "owned media specialist",
        "inbound marketing specialist",
        "inbound marketing manager",
        "messaging push notification specialist",
        "email marketing manager",
        "analista de mensageria whatsapp",
        "loyalty specialist",
        "loyalty manager",
        "especialista em programas de fidelidade",
        "gerente de programas de fidelidade",
        "customer journey specialist",
        "customer journey manager",
        "especialista de mapeamento de jornada",
        "customer experience specialist",
        "customer experience manager",
        "analista de voc voice of customer",
        "analista de nps",
        "cdp specialist",
        "customer data platform specialist",
        "customer data analyst",
        "customer intelligence specialist",
        "database marketing analyst",
        "analista de segmentacao consumidor",
        "martech data specialist",
        "product manager martech",
        "product manager lifecycle",
        "product manager growth",
        "product owner plataformas de marketing",
        "analista de crm marketing",
        "analista de marketing de relacionamento",
        "analista de regua de relacionamento",
        "analista de automacao de marketing",
        "analista de inbound marketing",
        "analista de lifecycle marketing",
        "analista de retencao e engajamento",
        "growth crm specialist",
        "retention specialist",
        "especialista em crm e ltv",
        "analista de crm data analytics",
        "analista de operacoes de crm",
        "crm ops",
        "especialista de growth e lifecycle",
        "especialista de canais digitais",
        "digital channels specialist",
        "analista de programas de fidelidade",
        "especialista em customer experience e crm",
        "analista de omnichannel",
        "coordenador de crm e growth",
        "coordenador de lifecycle marketing",
        "coordenador de marketing de relacionamento",
        "gerente de crm e martech",
        "gerente de lifecycle e retention",
        "head de crm e growth",
        "head de customer marketing",
        "head de lifecycle martech",
        "diretor de crm e customer experience",
        "crm lifecycle marketing manager",
        "customer retention specialist",
        "crm operations manager",
        "crm data analyst",
        "crm product owner",
        "crm", "analista de crm", "especialista crm", "gerente crm",
        "diretor crm", "head crm", "consultor crm", "desenvolvedor crm",
        "crm marketing", "marketing de relacionamento", "marketing automation",
        "jornada do cliente", "analista de campanhas", "lifecycle marketing",
        "salesforce", "salesforce administrator", "salesforce developer",
        "salesforce consultant", "analista salesforce", "marketing cloud",
        "hubspot", "analista hubspot", "especialista hubspot",
        "rd station", "analista rd station",
        "dynamics crm", "pipedrive", "activecampaign", "braze", "klaviyo",
        "growth crm", "crm analytics", "automacao de marketing",
        "implementacao crm", "loyalty crm",
    ]

    for query in searches:
        try:
            params = {"jobName": query, "limit": 20, "offset": 0, "isRemoteWork": "true"}
            resp = session.get(API_URL, params=params, timeout=(5, 10))
            if resp.status_code != 200:
                continue

            for job in resp.json().get("data", []):
                url = job.get("jobUrl", "") or f"https://portal.gupy.io/job/{job.get('id','')}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = job.get("name", "")
                if not title:
                    continue

                category = classify(title)
                if not category:
                    continue

                city = job.get("city", "")
                state = job.get("state", "")
                loc = f"{city}, {state}".strip(", ") if (city or state) else "Remoto"

                vagas.append({
                    "title": title,
                    "company": job.get("careerPageName", "Não informado"),
                    "url": url,
                    "location": loc,
                    "description": job.get("description", "")[:300],
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[Gupy] Erro em '{query}': {e}")

    print(f"[Gupy] {len(vagas)} vagas encontradas")
    return vagas
