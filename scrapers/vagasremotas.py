"""
Scraper para vagasremotas.net — board WordPress de vagas remotas BR.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "VagasRemotas"

CRM_SEARCHES = [
    "https://vagasremotas.net/?s=crm",
    "https://vagasremotas.net/?s=salesforce",
    "https://vagasremotas.net/?s=hubspot",
    "https://vagasremotas.net/?s=rd+station",
    "https://vagasremotas.net/?s=marketing+relacionamento",
    "https://vagasremotas.net/?s=crm+marketing",
    "https://vagasremotas.net/?s=braze",
    "https://vagasremotas.net/?s=klaviyo",
]

BASE_URL = "https://vagasremotas.net/category/oportunidades/"


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen: set[str] = set()

    import requests as _req
    session = _req.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    from bs4 import BeautifulSoup as _BS
    from .base import classify as _classify

    for url in CRM_SEARCHES:
        try:
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue
            soup = _BS(resp.text, "html.parser")
            articles = soup.select("article, div.post, div[class*='job'], li[class*='job']")
            for art in articles:
                title_el = art.select_one("h2, h3, h4, [class*='title']")
                link_el = art.select_one("a[href]")
                if not title_el or not link_el:
                    continue
                title = title_el.get_text(strip=True)
                job_url = link_el.get("href","")
                if not job_url or job_url in seen:
                    continue
                seen.add(job_url)
                category = _classify(title)
                if not category:
                    continue
                vagas.append({
                    "title": title,
                    "company": "Não informado",
                    "url": job_url,
                    "location": "Remoto",
                    "description": "",
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[VagasRemotas] Erro CRM '{url}': {e}")

    print(f"[VagasRemotas] {len(vagas)} vagas encontradas")
    return vagas


def _scrape_original() -> list[dict]:
    vagas_orig: list[dict] = []
    seen_orig: set[str] = set()
