"""
Scraper para Trampos.co — board de vagas criativas e tech do Brasil.
Usa a API pública v2: GET /api/v2/opportunities?home_office=true&per_page=50
A API retorna JSON com vagas remotas (home_office=True).

URL: https://trampos.co/api/v2/opportunities?home_office=true&per_page=50&page={n}
"""
import requests
from .base import classify

SOURCE = "Trampos"
API_URL = "https://trampos.co/api/v2/opportunities"
MAX_PAGES = 5


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen_ids: set = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://trampos.co/oportunidades",
    })

    for page in range(1, MAX_PAGES + 1):
        try:
            resp = session.get(
                API_URL,
                params={"home_office": "true", "per_page": 50, "page": page},
                timeout=(5, 12),
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("opportunities", [])
            if not jobs:
                break

            fresh = 0
            for job in jobs:
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                fresh += 1

                # Pula vagas que não são home office
                if not job.get("home_office") and job.get("city"):
                    continue

                title = job.get("name", "").strip()
                if not title:
                    continue

                company = job.get("custom_company_name") or ""
                if not company and job.get("company"):
                    company = (job["company"].get("name") or "") if isinstance(job["company"], dict) else str(job["company"])
                company = company.strip() or "Não informado"

                url = (
                    job.get("apply_url")
                    or f"https://trampos.co/oportunidade/{job_id}"
                )
                if not url.startswith("http"):
                    url = f"https://trampos.co/oportunidade/{job_id}"

                published_at = job.get("published_at")

                category = classify(title)
                if not category:
                    # Fallback: categoria via tag da API
                    cat_name = (job.get("category_name") or "").lower()
                    cat_slug = (job.get("category_slug") or "").lower()
                    if any(w in cat_name + cat_slug for w in ["design", "ux", "ui", "product"]):
                        category = "designer"
                    elif any(w in cat_name + cat_slug for w in ["atendimento", "customer", "cx", "cs"]):
                        category = "cxcs"
                    elif any(w in cat_name + cat_slug for w in ["desenvolvi", "tech", "software", "dados", "data"]):
                        category = "dev"
                    else:
                        continue

                vagas.append({
                    "title":        title,
                    "company":      company,
                    "url":          url,
                    "location":     "Remoto",
                    "description":  "",
                    "source":       SOURCE,
                    "category":     category,
                    "published_at": published_at,
                })

            if fresh == 0:
                break

        except Exception as e:
            print(f"[Trampos] página {page}: {e}")
            break

    print(f"[Trampos] {len(vagas)} vagas encontradas")
    return vagas
