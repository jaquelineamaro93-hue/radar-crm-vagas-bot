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
