"""Coleta focada em Product Design no Brasil (Gupy + LinkedIn publico).

Independente das centenas de buscas gerais, para que Product Design nao fique
sem atualizacao quando o radar completo excede o tempo da funcao.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from .base import is_product_design_title

SEARCH_TERMS = (
    "product designer",
    "designer de produto",
    "design de produto",
    "ux designer",
    "ui designer",
    "ux ui designer",
    "ux researcher",
    "service designer",
)
GUPY_ENDPOINTS = (
    "https://employability-portal.gupy.io/api/v1/jobs",
    "https://portal.api.gupy.io/api/v1/jobs",
)
LINKEDIN_ENDPOINT = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
}
MAX_VAGAS = 120


def _gupy(term: str) -> list[dict]:
    params = {"jobName": term, "limit": 20, "offset": 0}
    jobs = []
    for endpoint in GUPY_ENDPOINTS:
        try:
            resp = requests.get(endpoint, params=params, headers=HEADERS, timeout=(4, 9))
            if not resp.ok:
                continue
            payload = resp.json()
            data = payload.get("data", []) if isinstance(payload, dict) else []
            if isinstance(data, dict):
                data = data.get("data") or data.get("items") or []
            if isinstance(data, list):
                jobs = data
                if jobs:
                    break
        except (requests.RequestException, ValueError) as exc:
            print(f"[Design/Gupy] {term}: {exc}")

    result = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        title = job.get("name") or job.get("title") or ""
        if not is_product_design_title(title):
            continue
        identifier = job.get("id")
        url = job.get("jobUrl") or (f"https://portal.gupy.io/job/{identifier}" if identifier else "")
        if not url:
            continue
        place = ", ".join(part for part in (job.get("city"), job.get("state")) if part)
        result.append({
            "title": title,
            "company": job.get("careerPageName") or "Nao informado",
            "url": url,
            "location": place or "Brasil (modelo nao informado)",
            "description": (job.get("description") or "")[:300],
            "source": "Gupy",
            "category": "designer",
            "published_at": None,
        })
    return result


def _linkedin(term: str, start: int) -> list[dict]:
    params = {
        "keywords": term,
        "location": "Brazil",
        "f_TPR": "r2592000",  # ultimos 30 dias
        "start": start,
        # Sem f_WT: considera remoto, hibrido e presencial
    }
    try:
        resp = requests.get(LINKEDIN_ENDPOINT, params=params, headers=HEADERS, timeout=(4, 9))
        if not resp.ok:
            return []
    except requests.RequestException as exc:
        print(f"[Design/LinkedIn] {term} offset={start}: {exc}")
        return []

    result = []
    soup = BeautifulSoup(resp.text, "html.parser")
    for card in soup.select("li"):
        title_tag = card.select_one(".base-search-card__title, h3")
        link_tag = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
        if not title_tag or not link_tag:
            continue
        title = title_tag.get_text(strip=True)
        if not is_product_design_title(title):
            continue
        url = (link_tag.get("href") or "").split("?")[0]
        if not url.startswith("https://"):
            continue
        company_tag = card.select_one(".base-search-card__subtitle, h4")
        location_tag = card.select_one(".job-search-card__location")
        time_tag = card.select_one("time[datetime]")
        pub = time_tag.get("datetime") if time_tag else None
        if pub and len(pub) == 10:
            pub = pub + "T00:00:00+00:00"
        result.append({
            "title": title,
            "company": company_tag.get_text(strip=True) if company_tag else "Nao informado",
            "url": url,
            "location": location_tag.get_text(strip=True) if location_tag else "Brasil (modelo nao informado)",
            "description": "",
            "source": "LinkedIn",
            "category": "designer",
            "published_at": pub,
        })
    return result


def _fetch(task: tuple) -> list[dict]:
    platform, term, offset = task
    try:
        return _gupy(term) if platform == "gupy" else _linkedin(term, offset)
    except Exception as exc:
        print(f"[Design] Erro em {platform}/{term}: {exc}")
        return []


def scrape() -> list[dict]:
    tasks = [("gupy", term, 0) for term in SEARCH_TERMS]
    tasks += [("linkedin", term, start) for term in SEARCH_TERMS for start in (0, 25)]
    results = []
    seen = set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for batch in pool.map(_fetch, tasks):
            for vaga in batch:
                url = vaga["url"]
                if url in seen:
                    continue
                seen.add(url)
                if len(results) < MAX_VAGAS:
                    results.append(vaga)
    print(f"[Product Design] {len(results)} vagas unicas coletadas")
    return results
