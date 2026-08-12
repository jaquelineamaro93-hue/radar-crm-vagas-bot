"""
Scraper para Remotar.com.br — board de vagas remotas brasileiro.
Tenta JSON (Next.js / GraphQL inline) e, se falhar, faz parse HTML.
"""
import json
import re
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Remotar"
BASE_URL = "https://remotar.com.br"

# Sufixos de busca — o site usa /vagas/[categoria]
SEARCHES = [
    "/vagas/design",
    "/vagas/customer-success",
    "/vagas/customer-experience",
    "/vagas/marketing",         # CX/CS overflow
    "/vagas/desenvolvimento",
    "/vagas/dados",
    "/vagas",                   # listagem geral (captura o resto)
]


def _extract_next_jobs(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"id": "__NEXT_DATA__"}):
        try:
            data = json.loads(script.string or "")
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
        "div.job-card", "article.job", "li.job",
        "div[class*='JobCard']", "div[class*='job-card']",
        "div[class*='vacancy']", "li[class*='job']",
        "article[class*='opportunity']",
    ]
    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break

    if not cards:
        # Fallback: qualquer container com link + h2/h3
        for h in soup.select("h2, h3"):
            a = h.find("a") or (h.parent and h.parent.find("a"))
            if a and a.get("href", "").startswith("/"):
                cards.append(h.parent)

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

        category = classify(title)
        if not category:
            continue

        time_el = card.select_one("time[datetime]")
        published_at = time_el.get("datetime") if time_el else None

        vagas.append({
            "title": title,
            "company": company,
            "url": url,
            "location": "Remoto",
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
            print(f"[Remotar] {path}: {e}")

    print(f"[Remotar] {len(vagas)} vagas encontradas")
    return vagas
