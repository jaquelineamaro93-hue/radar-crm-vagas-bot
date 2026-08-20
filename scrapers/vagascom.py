"""
Scraper para Vagas.com.br — focado em CRM.
Usa o atributo title= do link para pegar o título correto.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Vagas.com"
BASE_URL = "https://www.vagas.com.br"

SEARCHES = [
    "vagas-de-crm",
    "vagas-de-salesforce",
    "vagas-de-hubspot",
    "vagas-de-rd-station",
    "vagas-de-marketing-de-relacionamento",
    "vagas-de-crm-marketing",
    "vagas-de-marketing-automation",
    "vagas-de-braze",
    "vagas-de-klaviyo",
    "vagas-de-pipedrive",
    "vagas-de-dynamics-crm",
    "vagas-de-analista-de-campanhas",
]

def scrape() -> list[dict]:
    vagas = []
    seen = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for slug in SEARCHES:
        try:
            url = f"{BASE_URL}/{slug}"
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("h2.cargo a.link-detalhes-vaga")

            for link in links:
                title = link.get("title", "").strip()
                if not title:
                    title = link.get_text(separator=" ", strip=True)
                if not title:
                    continue

                href = link.get("href", "")
                job_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if not job_url or job_url in seen:
                    continue
                seen.add(job_url)

                category = classify(title)
                if not category:
                    continue

                company_el = soup.select_one(f"#{link.get('id','')} ~ span.emprVaga") if link.get("id") else None
                company = company_el.get_text(strip=True) if company_el else "Não informado"

                vagas.append({
                    "title": title,
                    "company": company,
                    "url": job_url,
                    "location": "Brasil",
                    "description": "",
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[Vagas.com] Erro '{slug}': {e}")

    print(f"[Vagas.com] {len(vagas)} vagas encontradas")
    return vagas
