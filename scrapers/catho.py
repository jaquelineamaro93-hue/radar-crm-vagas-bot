"""
Scraper para Catho.com.br — focado em CRM.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Catho"
BASE_URL = "https://www.catho.com.br"

SEARCHES = [
    "crm", "salesforce", "hubspot", "rd-station",
    "crm-marketing", "marketing-de-relacionamento",
    "marketing-automation", "analista-de-campanhas",
    "braze", "klaviyo", "pipedrive",
]

def scrape() -> list[dict]:
    vagas = []
    seen = set()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    for q in SEARCHES:
        try:
            url = f"{BASE_URL}/vagas/home-office/?q={q}"
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("article, div[class*='JobCard'], div[class*='job-card'], li[class*='job']")
            for card in cards:
                title_el = card.select_one("h2, h3, [class*='title'], [class*='Title'], [class*='name']")
                link_el = card.select_one("a[href]")
                if not title_el or not link_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue
                href = link_el.get("href", "")
                url_vaga = f"{BASE_URL}{href}" if href.startswith("/") else href
                if url_vaga in seen:
                    continue
                seen.add(url_vaga)
                category = classify(title)
                if not category:
                    continue
                company_el = card.select_one("[class*='company'], [class*='Company'], [class*='employer']")
                company = company_el.get_text(strip=True) if company_el else "Não informado"
                vagas.append({
                    "title": title,
                    "company": company,
                    "url": url_vaga,
                    "location": "Remoto",
                    "description": "",
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[Catho] Erro '{q}': {e}")
    print(f"[Catho] {len(vagas)} vagas encontradas")
    return vagas
