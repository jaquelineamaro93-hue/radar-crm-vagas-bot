"""
Scraper para Solides Vagas (vagas.solides.com.br).
"""
import json
import requests
from bs4 import BeautifulSoup
from base import classify

SOURCE = "Solides"
BASE_URL = "https://vagas.solides.com.br"

SEARCHES = ["crm", "salesforce", "hubspot", "rd-station", "marketing-de-relacionamento"]


def scrape() -> list[dict]:
    vagas = []
    seen: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for term in SEARCHES:
        for page in range(1, 4):
            try:
                url = f"{BASE_URL}/vagas/todos/{term}?page={page}"
                resp = session.get(url, timeout=(5, 12))
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                script = soup.find("script", {"id": "__NEXT_DATA__"})
                if not script or not script.string:
                    break

                data = json.loads(script.string)
                pp = data.get("props", {}).get("pageProps", {})

                jobs = []
                for key in ("jobs", "vacancies", "data", "results", "items"):
                    val = pp.get(key)
                    if isinstance(val, list) and val:
                        jobs = val
                        break
                    if isinstance(val, dict):
                        for sub in val.values():
                            if isinstance(sub, list) and sub:
                                jobs = sub
                                break

                if not jobs:
                    break

                for job in jobs:
                    title = job.get("title") or job.get("name") or job.get("position") or ""
                    if not title:
                        continue

                    slug = job.get("slug") or str(job.get("id", ""))
                    job_url = job.get("url") or f"{BASE_URL}/vaga/{slug}"
                    if not job_url or job_url in seen:
                        continue
                    seen.add(job_url)

                    company = job.get("company") or job.get("companyName") or "Não informado"
                    if isinstance(company, dict):
                        company = company.get("name") or "Não informado"

                    category = classify(title)
                    if not category:
                        continue

                    vagas.append({
                        "title": title,
                        "company": company,
                        "url": job_url,
                        "location": job.get("location") or job.get("city") or "Não informado",
                        "description": (job.get("description") or "")[:300],
                        "source": SOURCE,
                        "category": category,
                        "published_at": job.get("publishedAt") or job.get("createdAt"),
                    })
            except Exception as e:
                print(f"[Solides] {term} p{page}: {e}")
                break

    print(f"[Solides] {len(vagas)} vagas encontradas")
    return vagas
