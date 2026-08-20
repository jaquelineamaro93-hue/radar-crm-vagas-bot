"""
Scraper para VagasRemotas.net — focado em CRM.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "VagasRemotas"
BASE_URL = "https://vagasremotas.net"

CRM_SEARCHES = [
    "crm", "salesforce", "hubspot", "rd station",
    "crm marketing", "marketing de relacionamento",
    "braze", "klaviyo", "marketing automation",
    "analista de campanhas",
]

def scrape() -> list[dict]:
    vagas = []
    seen = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for term in CRM_SEARCHES:
        try:
            url = f"{BASE_URL}/?s={term.replace(' ', '+')}"
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.select("article, h2.entry-title, .post-title")
            for art in articles:
                title_el = art.select_one("h2, h3, h4, .entry-title")
                link_el = art.select_one("a[href]")
                if not title_el or not link_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue
                href = link_el.get("href", "")
                if not href or href in seen:
                    continue
                seen.add(href)
                category = classify(title)
                if not category:
                    continue
                vagas.append({
                    "title": title,
                    "company": "Não informado",
                    "url": href,
                    "location": "Remoto",
                    "description": "",
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[VagasRemotas] Erro '{term}': {e}")

    print(f"[VagasRemotas] {len(vagas)} vagas encontradas")
    return vagas
