"""
Scraper para LinkedIn Jobs (busca pública, sem login).
"""
import time
import requests
from .base import classify, relative_to_iso

SOURCE = "LinkedIn"

# (keyword, location, f_WT, f_TPR)
# f_WT: "1"=presencial, "2"=remoto
# f_TPR: r2592000=30d, r5184000=60d
SEARCHES = [
    ("forward deployed engineer", "Brazil", "2", "r5184000"),
    ("fde ai martech", "Brazil", "2", "r5184000"),
    ("ai agent architect", "Brazil", "2", "r5184000"),
    ("ai agent product manager", "Brazil", "2", "r5184000"),
    ("ai solutions architect crm", "Brazil", "2", "r5184000"),
    ("desenvolvedor de agentes de ia", "Brazil", "2", "r5184000"),
    ("engenheiro de integracao de agentes", "Brazil", "2", "r5184000"),
    ("especialista em crm e inteligencia artificial", "Brazil", "2", "r5184000"),
    ("ai lifecycle marketing", "Brazil", "2", "r5184000"),
    ("crm preditivo", "Brazil", "2", "r5184000"),
    ("predictive crm specialist", "Brazil", "2", "r5184000"),
    ("ai-driven growth specialist", "Brazil", "2", "r5184000"),
    ("analista de dados de crm machine learning", "Brazil", "2", "r5184000"),
    ("real-time personalization specialist", "Brazil", "2", "r5184000"),
    ("ia conversacional", "Brazil", "2", "r5184000"),
    ("conversational ai specialist", "Brazil", "2", "r5184000"),
    ("prompt engineer crm", "Brazil", "2", "r5184000"),
    ("prompt engineer cx", "Brazil", "2", "r5184000"),
    ("conversational ai product owner", "Brazil", "2", "r5184000"),
    ("automacao de atendimento ia generativa", "Brazil", "2", "r5184000"),
    ("arquiteto de bots agentes autonomos", "Brazil", "2", "r5184000"),
    ("ai martech operations specialist", "Brazil", "2", "r5184000"),
    ("cdp ai data specialist", "Brazil", "2", "r5184000"),
    ("orquestracao de agentes crm", "Brazil", "2", "r5184000"),
    ("engenheiro de dados de consumidor ia", "Brazil", "2", "r5184000"),
    ("head of ai customer experience", "Brazil", "2", "r5184000"),
    ("head of ai-driven crm", "Brazil", "2", "r5184000"),
    ("tech lead agentes de ia", "Brazil", "2", "r5184000"),
    ("gerente de agentes de ia", "Brazil", "2", "r5184000"),
    ("lifecycle marketing specialist", "Brazil", "2", "r5184000"),
    ("lifecycle marketing manager", "Brazil", "2", "r5184000"),
    ("retention marketing specialist", "Brazil", "2", "r5184000"),
    ("retention marketing manager", "Brazil", "2", "r5184000"),
    ("especialista em engajamento e reativacao", "Brazil", "2", "r5184000"),
    ("especialista de prevencao a churn", "Brazil", "2", "r5184000"),
    ("churn specialist", "Brazil", "2", "r5184000"),
    ("customer marketing specialist", "Brazil", "2", "r5184000"),
    ("customer marketing manager", "Brazil", "2", "r5184000"),
    ("monetizacao de base", "Brazil", "2", "r5184000"),
    ("marketing automation specialist", "Brazil", "2", "r5184000"),
    ("marketing automation architect", "Brazil", "2", "r5184000"),
    ("especialista de martech", "Brazil", "2", "r5184000"),
    ("analista de martech", "Brazil", "2", "r5184000"),
    ("marketing operations analyst", "Brazil", "2", "r5184000"),
    ("marketing operations manager", "Brazil", "2", "r5184000"),
    ("marketing ops", "Brazil", "2", "r5184000"),
    ("arquiteto de solucoes de marketing", "Brazil", "2", "r5184000"),
    ("growth marketing manager", "Brazil", "2", "r5184000"),
    ("growth marketing specialist", "Brazil", "2", "r5184000"),
    ("retention growth manager", "Brazil", "2", "r5184000"),
    ("ltv specialist", "Brazil", "2", "r5184000"),
    ("ltv manager", "Brazil", "2", "r5184000"),
    ("product growth analyst", "Brazil", "2", "r5184000"),
    ("especialista em canais proprietarios", "Brazil", "2", "r5184000"),
    ("owned media specialist", "Brazil", "2", "r5184000"),
    ("inbound marketing specialist", "Brazil", "2", "r5184000"),
    ("inbound marketing manager", "Brazil", "2", "r5184000"),
    ("messaging push notification specialist", "Brazil", "2", "r5184000"),
    ("email marketing manager", "Brazil", "2", "r5184000"),
    ("analista de mensageria whatsapp", "Brazil", "2", "r5184000"),
    ("loyalty specialist", "Brazil", "2", "r5184000"),
    ("loyalty manager", "Brazil", "2", "r5184000"),
    ("especialista em programas de fidelidade", "Brazil", "2", "r5184000"),
    ("gerente de programas de fidelidade", "Brazil", "2", "r5184000"),
    ("customer journey specialist", "Brazil", "2", "r5184000"),
    ("customer journey manager", "Brazil", "2", "r5184000"),
    ("especialista de mapeamento de jornada", "Brazil", "2", "r5184000"),
    ("customer experience specialist", "Brazil", "2", "r5184000"),
    ("customer experience manager", "Brazil", "2", "r5184000"),
    ("analista de voc voice of customer", "Brazil", "2", "r5184000"),
    ("analista de nps", "Brazil", "2", "r5184000"),
    ("cdp specialist", "Brazil", "2", "r5184000"),
    ("customer data platform specialist", "Brazil", "2", "r5184000"),
    ("customer data analyst", "Brazil", "2", "r5184000"),
    ("customer intelligence specialist", "Brazil", "2", "r5184000"),
    ("database marketing analyst", "Brazil", "2", "r5184000"),
    ("analista de segmentacao consumidor", "Brazil", "2", "r5184000"),
    ("martech data specialist", "Brazil", "2", "r5184000"),
    ("product manager martech", "Brazil", "2", "r5184000"),
    ("product manager lifecycle", "Brazil", "2", "r5184000"),
    ("product manager growth", "Brazil", "2", "r5184000"),
    ("product owner plataformas de marketing", "Brazil", "2", "r5184000"),
    ("analista de crm marketing", "Brazil", "2", "r5184000"),
    ("analista de marketing de relacionamento", "Brazil", "2", "r5184000"),
    ("analista de regua de relacionamento", "Brazil", "2", "r5184000"),
    ("analista de automacao de marketing", "Brazil", "2", "r5184000"),
    ("analista de inbound marketing", "Brazil", "2", "r5184000"),
    ("analista de lifecycle marketing", "Brazil", "2", "r5184000"),
    ("analista de retencao e engajamento", "Brazil", "2", "r5184000"),
    ("growth crm specialist", "Brazil", "2", "r5184000"),
    ("retention specialist", "Brazil", "2", "r5184000"),
    ("especialista em crm e ltv", "Brazil", "2", "r5184000"),
    ("analista de crm data analytics", "Brazil", "2", "r5184000"),
    ("analista de operacoes de crm", "Brazil", "2", "r5184000"),
    ("crm ops", "Brazil", "2", "r5184000"),
    ("especialista de growth e lifecycle", "Brazil", "2", "r5184000"),
    ("especialista de canais digitais", "Brazil", "2", "r5184000"),
    ("digital channels specialist", "Brazil", "2", "r5184000"),
    ("analista de programas de fidelidade", "Brazil", "2", "r5184000"),
    ("especialista em customer experience e crm", "Brazil", "2", "r5184000"),
    ("analista de omnichannel", "Brazil", "2", "r5184000"),
    ("coordenador de crm e growth", "Brazil", "2", "r5184000"),
    ("coordenador de lifecycle marketing", "Brazil", "2", "r5184000"),
    ("coordenador de marketing de relacionamento", "Brazil", "2", "r5184000"),
    ("gerente de crm e martech", "Brazil", "2", "r5184000"),
    ("gerente de lifecycle e retention", "Brazil", "2", "r5184000"),
    ("head de crm e growth", "Brazil", "2", "r5184000"),
    ("head de customer marketing", "Brazil", "2", "r5184000"),
    ("head de lifecycle martech", "Brazil", "2", "r5184000"),
    ("diretor de crm e customer experience", "Brazil", "2", "r5184000"),
    ("crm lifecycle marketing manager", "Brazil", "2", "r5184000"),
    ("customer retention specialist", "Brazil", "2", "r5184000"),
    ("crm operations manager", "Brazil", "2", "r5184000"),
    ("crm data analyst", "Brazil", "2", "r5184000"),
    ("crm product owner", "Brazil", "2", "r5184000"),
    # CRM genérico
    ("crm", "Brazil", "2", "r5184000"),
    ("analista de crm", "Brazil", "2", "r5184000"),
    ("especialista crm", "Brazil", "2", "r5184000"),
    ("coordenador crm", "Brazil", "2", "r5184000"),
    ("gerente crm", "Brazil", "2", "r5184000"),
    ("diretor crm", "Brazil", "2", "r5184000"),
    ("head crm", "Brazil", "2", "r5184000"),
    ("consultor crm", "Brazil", "2", "r5184000"),
    ("desenvolvedor crm", "Brazil", "2", "r5184000"),
    ("crm manager", "Brazil", "2", "r5184000"),
    ("crm specialist", "Brazil", "2", "r5184000"),
    ("crm analyst", "Brazil", "2", "r5184000"),
    ("crm director", "Brazil", "2", "r5184000"),
    ("crm lead", "Brazil", "2", "r5184000"),
    # CRM Marketing / Relacionamento
    ("crm marketing", "Brazil", "2", "r5184000"),
    ("marketing de relacionamento", "Brazil", "2", "r5184000"),
    ("marketing automation", "Brazil", "2", "r5184000"),
    ("automacao de marketing", "Brazil", "2", "r5184000"),
    ("lifecycle marketing", "Brazil", "2", "r5184000"),
    ("jornada do cliente", "Brazil", "2", "r5184000"),
    ("analista de campanhas", "Brazil", "2", "r5184000"),
    ("growth crm", "Brazil", "2", "r5184000"),
    ("crm analytics", "Brazil", "2", "r5184000"),
    ("canais digitais crm", "Brazil", "2", "r5184000"),
    # Salesforce
    ("salesforce", "Brazil", "2", "r5184000"),
    ("salesforce administrator", "Brazil", "2", "r5184000"),
    ("salesforce developer", "Brazil", "2", "r5184000"),
    ("salesforce consultant", "Brazil", "2", "r5184000"),
    ("analista salesforce", "Brazil", "2", "r5184000"),
    ("marketing cloud", "Brazil", "2", "r5184000"),
    ("salesforce marketing cloud", "Brazil", "2", "r5184000"),
    ("agentforce", "Brazil", "2", "r5184000"),
    # HubSpot
    ("hubspot", "Brazil", "2", "r5184000"),
    ("analista hubspot", "Brazil", "2", "r5184000"),
    ("hubspot administrator", "Brazil", "2", "r5184000"),
    # RD Station
    ("rd station", "Brazil", "2", "r5184000"),
    ("analista rd station", "Brazil", "2", "r5184000"),
    # Outras plataformas CRM
    ("dynamics crm", "Brazil", "2", "r5184000"),
    ("pipedrive", "Brazil", "2", "r5184000"),
    ("activecampaign", "Brazil", "2", "r5184000"),
    ("braze", "Brazil", "2", "r5184000"),
    ("klaviyo", "Brazil", "2", "r5184000"),
    ("oracle responsys", "Brazil", "2", "r5184000"),
    # Implementação / Dev CRM
    ("implementacao crm", "Brazil", "2", "r5184000"),
    ("analista funcional crm", "Brazil", "2", "r5184000"),
    ("loyalty crm", "Brazil", "2", "r5184000"),
    ("fidelizacao clientes", "Brazil", "2", "r5184000"),
]

BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def scrape() -> list[dict]:
    vagas = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for keyword, location, f_wt, f_tpr in SEARCHES:
        params = {
            "keywords": keyword,
            "location": location,
            "f_WT": f_wt,
            "f_TPR": f_tpr,
            "start": 0,
        }
        try:
            resp = session.get(BASE_URL, params=params, timeout=(5, 8))
            if resp.status_code != 200:
                continue
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.select("li"):
                title_el = card.select_one(".base-search-card__title, h3")
                company_el = card.select_one(".base-search-card__subtitle, h4")
                location_el = card.select_one(".job-search-card__location")
                time_el = card.select_one("time[datetime]")
                link_el = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Não informado"
                loc = location_el.get_text(strip=True) if location_el else "Remoto"
                url = link_el.get("href", "").split("?")[0]

                # Data de publicação
                published_at = None
                if time_el:
                    published_at = time_el.get("datetime")  # formato: "2024-01-15"
                    if published_at and len(published_at) == 10:
                        published_at = published_at + "T00:00:00+00:00"

                category = classify(title)
                if not category:
                    continue

                vagas.append({
                    "title": title, "company": company,
                    "url": url, "location": loc,
                    "description": "", "source": SOURCE,
                    "category": category, "published_at": published_at,
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"[LinkedIn] {keyword}: {e}")

    print(f"[LinkedIn] {len(vagas)} vagas encontradas")
    return vagas
