"""
Scraper dedicado a vagas de Automação Industrial.
  - automacao_presencial: Engenheiro de Automação Industrial (on-site, f_WT=1)
  - automacao_remote:     Projetista de Automação (home office, f_WT=2)
Categoria definida pela busca, não por classify(), para evitar cruzamento.
"""
import time
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "LinkedIn"
_AUTOMATION_CATS = {"automacao_presencial", "automacao_remote"}
BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

# (keyword, linkedin_f_WT, category)
# f_WT=1 = on-site | f_WT=2 = remote
SEARCHES = [
    # ── Engenheiro de Automação Industrial — PRESENCIAL ──────────────────
    ("engenheiro automação industrial",      "1", "automacao_presencial"),
    ("engenheiro de automação",              "1", "automacao_presencial"),
    ("engenheiro controle automação",        "1", "automacao_presencial"),
    ("programador PLC CLP SCADA",           "1", "automacao_presencial"),
    ("instrumentação controle industrial",   "1", "automacao_presencial"),
    ("engenheiro mecatrônico automação",     "1", "automacao_presencial"),
    # ── Projetista de Automação — HOME OFFICE ────────────────────────────
    ("projetista de automação",             "2", "automacao_remote"),
    ("projetista elétrico industrial",      "2", "automacao_remote"),
    ("projetista EPLAN remoto",             "2", "automacao_remote"),
    ("projetista painéis elétricos",        "2", "automacao_remote"),
    ("projetista AutoCAD Electrical",       "2", "automacao_remote"),
]


def _parse_cards(html: str, category: str, seen: set) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    vagas = []

    for card in soup.select("li"):
        title_el   = card.select_one(".base-search-card__title, h3")
        company_el = card.select_one(".base-search-card__subtitle, h4")
        location_el = card.select_one(".job-search-card__location")
        time_el    = card.select_one("time[datetime]")
        link_el    = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")

        if not title_el or not link_el:
            continue

        url = link_el.get("href", "").split("?")[0]
        if url in seen:
            continue
        seen.add(url)

        title   = title_el.get_text(strip=True)

        # Rejeita vagas cujo título não contenha nenhuma keyword de automação
        if classify(title) not in _AUTOMATION_CATS:
            continue

        company = company_el.get_text(strip=True) if company_el else "Não informado"
        loc     = location_el.get_text(strip=True) if location_el else (
            "Presencial" if category == "automacao_presencial" else "Remoto"
        )

        published_at = None
        if time_el:
            published_at = time_el.get("datetime")
            if published_at and len(published_at) == 10:
                published_at += "T00:00:00+00:00"

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
    seen_urls: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for keyword, f_wt, category in SEARCHES:
        params = {
            "keywords":  keyword,
            "location":  "Brazil",
            "f_WT":      f_wt,
            "f_TPR":     "r2592000",  # last 30 days
            "start":     0,
        }
        try:
            resp = session.get(BASE_URL, params=params, timeout=(5, 8))
            if resp.status_code != 200:
                continue
            vagas.extend(_parse_cards(resp.text, category, seen_urls))
            time.sleep(0.3)
        except Exception as e:
            print(f"[Automation] {keyword}: {e}")

    # ── Gupy ────────────────────────────────────────────────────────────────
    vagas.extend(_scrape_gupy(seen_urls))

    presencial = sum(1 for v in vagas if v["category"] == "automacao_presencial")
    remote     = sum(1 for v in vagas if v["category"] == "automacao_remote")
    print(f"[Automation] {len(vagas)} vagas — {presencial} presenciais, {remote} home office")
    return vagas


def _scrape_gupy(seen_urls: set) -> list[dict]:
    vagas = []
    API_URL = "https://portal.api.gupy.io/api/v1/jobs"
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://portal.gupy.io",
        "Referer": "https://portal.gupy.io/",
    })

    gupy_searches = [
        ("engenheiro de automação", False, "automacao_presencial"),
        ("automação industrial",    False, "automacao_presencial"),
        ("projetista de automação", True,  "automacao_remote"),
        ("projetista elétrico",     True,  "automacao_remote"),
    ]

    for query, is_remote, category in gupy_searches:
        try:
            params = {
                "jobName": query,
                "limit": 20,
                "offset": 0,
            }
            if is_remote:
                params["isRemoteWork"] = "true"

            resp = session.get(API_URL, params=params, timeout=(5, 8))
            if resp.status_code != 200:
                continue

            for job in resp.json().get("data", []):
                title_job = job.get("name", "")
                if classify(title_job) not in _AUTOMATION_CATS:
                    continue

                url = job.get("jobUrl", "") or f"https://portal.gupy.io/job/{job.get('id','')}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                city  = job.get("city", "")
                state = job.get("state", "")
                loc   = f"{city}, {state}".strip(", ") if (city or state) else (
                    "Remoto" if is_remote else "Presencial"
                )

                vagas.append({
                    "title":        title_job,
                    "company":      job.get("careerPageName", "Não informado"),
                    "url":          url,
                    "location":     loc,
                    "description":  job.get("description", "")[:300],
                    "source":       "Gupy",
                    "category":     category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[Automation/Gupy] {query}: {e}")

    return vagas
