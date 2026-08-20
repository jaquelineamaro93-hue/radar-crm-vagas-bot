"""
Scraper para 99jobs.com — focado em CRM.
"""
import json
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "99jobs"
BASE_URL = "https://99jobs.com"

SEARCHES = ["crm", "salesforce", "hubspot", "rd+station", "marketing+de+relacionamento", "braze", "klaviyo"]

def scrape() -> list[dict]:
    vagas = []
    seen = set()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    for q in SEARCHES:
        try:
            url = f"{BASE_URL}/opportunities?q={q}&remote=true"
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            # Tentar __NEXT_DATA__
            script = soup.find("script", {"id": "__NEXT_DATA__"})
            if script and script.string:
                data = json.loads(script.string)
                pp = data.get("props", {}).get("pageProps", {})
                jobs = pp.get("opportunities") or pp.get("jobs") or pp.get("data") or []
                if isinstance(jobs, dict):
                    jobs = jobs.get("data") or jobs.get("items") or []
                for job in jobs:
                    title = job.get("title") or job.get("name") or ""
                    if not title:
                        continue
                    url_vaga = job.get("url") or f"{BASE_URL}/opportunities/{job.get('id','')}"
                    if url_vaga in seen:
                        continue
                    seen.add(url_vaga)
                    category = classify(title)
                    if not category:
                        continue
                    company = job.get("company") or job.get("companyName") or "Não informado"
                    if isinstance(company, dict):
                        company = company.get("name") or "Não informado"
                    vagas.append({
                        "title": title,
                        "company": company,
                        "url": url_vaga,
                        "location": job.get("location") or "Remoto",
                        "description": (job.get("description") or "")[:300],
                        "source": SOURCE,
                        "category": category,
                        "published_at": job.get("publishedAt") or job.get("createdAt"),
                    })
            else:
                # Parse HTML
                cards = soup.select("div.opportunity-card, article.job, div.job-card, li.opportunity")
                for card in cards:
                    title_el = card.select_one("h2, h3, [class*='title'], [class*='Title']")
                    link_el = card.select_one("a[href]")
                    if not title_el or not link_el:
                        continue
                    title = title_el.get_text(strip=True)
                    href = link_el.get("href", "")
                    url_vaga = f"{BASE_URL}{href}" if href.startswith("/") else href
                    if url_vaga in seen:
                        continue
                    seen.add(url_vaga)
                    category = classify(title)
                    if not category:
                        continue
                    vagas.append({
                        "title": title,
                        "company": "Não informado",
                        "url": url_vaga,
                        "location": "Remoto",
                        "description": "",
                        "source": SOURCE,
                        "category": category,
                        "published_at": None,
                    })
        except Exception as e:
            print(f"[99jobs] Erro '{q}': {e}")
    print(f"[99jobs] {len(vagas)} vagas encontradas")
    return vagas
