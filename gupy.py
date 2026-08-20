"""
Scraper para Gupy — focado em CRM e áreas correlatas.
"""
import requests
from base import classify

SOURCE = "Gupy"
API_URL = "https://portal.api.gupy.io/api/v1/jobs"


def scrape() -> list[dict]:
    vagas = []
    seen_urls: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
    })

    searches = [
        "crm", "analista de crm", "especialista crm", "gerente crm",
        "diretor crm", "head crm", "consultor crm", "desenvolvedor crm",
        "crm marketing", "marketing de relacionamento", "marketing automation",
        "jornada do cliente", "canais digitais", "analista de campanhas",
        "salesforce", "salesforce administrator", "salesforce developer",
        "salesforce consultant", "analista salesforce", "marketing cloud",
        "hubspot", "analista hubspot", "especialista hubspot",
        "rd station", "analista rd station",
        "dynamics crm", "pipedrive", "activecampaign", "braze", "klaviyo",
        "growth crm", "crm analytics", "lifecycle marketing",
        "automacao de marketing", "implementacao crm",
    ]

    for query in searches:
        try:
            params = {"jobName": query, "limit": 20, "offset": 0, "isRemoteWork": "true"}
            resp = session.get(API_URL, params=params, timeout=(5, 8))
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
