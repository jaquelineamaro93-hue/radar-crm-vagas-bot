"""
Scraper para InHire.io — board de tech e design no Brasil.
Tenta extrair vagas via Next.js __NEXT_DATA__ e fallback HTML.
"""
import json
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "InHire"
BASE_URL = "https://inhire.io"

# Paths de busca — inhire usa /vagas?categoria=&remote=true
SEARCHES = [
    "/vagas?remote=true",
    "/vagas?area=design&remote=true",
    "/vagas?area=desenvolvimento&remote=true",
    "/vagas?area=dados&remote=true",
    "/vagas?area=customer-success&remote=true",
    "/vagas?area=crm&remote=true",
]


def _extract_next_jobs(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        return []
    try:
        data = json.loads(script.string)
        pp = data.get("props", {}).get("pageProps", {})
        for key in ("jobs", "vacancies", "opportunities", "data"):
            v = pp.get(key)
            if isinstance(v, list) and v:
                return v
            if isinstance(v, dict):
                for sub in v.values():
                    if isinstance(sub, list) and sub:
                        return sub
    except Exception:
        pass
    return []


def _parse_html(html: str, seen: set) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    vagas = []

    card_selectors = [
        "div.job-card", "article.job", "li.job-item",
        "div[class*='JobCard']", "div[class*='job-card']",
        "div[class*='VacancyCard']", "div[class*='vacancy']",
        "li[class*='job']",
    ]
    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break

    for card in cards:
        title_el = card.select_one(
            "h2, h3, [class*='title'], [class*='Title'], [class*='position']"
        )
        link_el = card.select_one("a[href]")
        if not title_el or not link_el:
            continue

        href = link_el.get("href", "")
        url = f"{BASE_URL}{href}" if href.startswith("/") else href
        if not url or url in seen:
            continue
        seen.add(url)

        title = title_el.get_text(strip=True)
        company_el = card.select_one(
            "[class*='company'], [class*='Company'], [class*='employer']"
        )
        company = company_el.get_text(strip=True) if company_el else "Não informado"
        location_el = card.select_one("[class*='location'], [class*='Location']")
        loc = location_el.get_text(strip=True) if location_el else "Remoto"

        category = classify(title)
        if not category:
            continue

        time_el = card.select_one("time[datetime]")
        published_at = time_el.get("datetime") if time_el else None

        vagas.append({
            "title": title,
            "company": company,
            "url": url,
            "location": loc,
            "description": "",
            "source": SOURCE,
            "category": category,
            "published_at": published_at,
        })

    return vagas


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    for path in SEARCHES:
        url = f"{BASE_URL}{path}"
        try:
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue

            jobs = _extract_next_jobs(resp.text)
            if jobs:
                for job in jobs:
                    title = job.get("title") or job.get("name") or job.get("position", "")
                    if not title:
                        continue
                    company = job.get("company") or job.get("company_name") or "Não informado"
                    if isinstance(company, dict):
                        company = company.get("name") or "Não informado"
                    slug = job.get("slug") or str(job.get("id", ""))
                    job_url = job.get("url") or (f"{BASE_URL}/vaga/{slug}" if slug else "")
                    if not job_url or job_url in seen:
                        continue
                    seen.add(job_url)
                    category = classify(title)
                    if not category:
                        continue
                    vagas.append({
                        "title": title,
                        "company": company,
                        "url": job_url,
                        "location": "Remoto",
                        "description": "",
                        "source": SOURCE,
                        "category": category,
                        "published_at": job.get("published_at") or job.get("created_at"),
                    })
            else:
                vagas.extend(_parse_html(resp.text, seen))

        except Exception as e:
            print(f"[InHire] {path}: {e}")

    print(f"[InHire] {len(vagas)} vagas encontradas")
    return vagas
