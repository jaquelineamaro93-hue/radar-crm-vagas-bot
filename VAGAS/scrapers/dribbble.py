"""
Scraper para Dribbble Jobs — board de design internacional.
Estrutura real (2025):
  li.job-list-item
    a.job-link[href=/jobs/{id}-{slug}]
    h4.job-title.job-board-job-title        → título
    span.job-board-job-company               → empresa
    span.location  (ou div.location-container) → localização

Filtra apenas vagas remotas. Inclui vagas internacionais (candidatos BR podem se candidatar).
"""
import re
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Dribbble"
BASE_URL = "https://dribbble.com"

# Buscas por área — /jobs?q=&remote=true retorna todos os remotos
SEARCHES = [
    ("ux designer",          True),
    ("product designer",     True),
    ("ui designer",          True),
    ("graphic designer",     True),
    ("web designer",         True),
    ("motion designer",      True),
    ("visual designer",      True),
    ("brand designer",       True),
    ("",                     True),   # Todos os remotos (página geral)
]

_REMOTE_WORDS = {"remote", "remoto", "work from anywhere", "anywhere"}


def _is_remote(loc: str) -> bool:
    lower = loc.lower()
    return any(w in lower for w in _REMOTE_WORDS)


def _parse_page(html: str, seen: set) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    vagas = []

    for card in soup.select("li.job-list-item"):
        # URL
        link_el = card.select_one("a.job-link")
        if not link_el:
            continue
        href = link_el.get("href", "").split("?")[0]
        url = f"{BASE_URL}{href}" if href.startswith("/") else href
        if not url or url in seen:
            continue

        # Título
        h4 = card.select_one("h4.job-title, h4.job-board-job-title, h3")
        if not h4:
            continue
        title = h4.get_text(strip=True)
        if not title:
            continue

        # Empresa
        comp_el = card.select_one("span.job-board-job-company")
        company = comp_el.get_text(strip=True) if comp_el else "Não informado"

        # Localização (prefer o container de detalhes adicionais)
        loc_el = (
            card.select_one(".job-additional-details-container span.location")
            or card.select_one("span.location")
            or card.select_one("div.location-container")
        )
        location = loc_el.get_text(strip=True) if loc_el else ""

        if not _is_remote(location):
            continue

        category = classify(title)
        if not category:
            continue

        seen.add(url)
        vagas.append({
            "title":        title,
            "company":      company or "Não informado",
            "url":          url,
            "location":     location or "Remoto",
            "description":  "",
            "source":       SOURCE,
            "category":     category,
            "published_at": None,   # Dribbble não expõe data na listagem
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
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    for query, remote in SEARCHES:
        try:
            params: dict = {}
            if remote:
                params["remote"] = "true"
            if query:
                params["q"] = query

            resp = session.get(f"{BASE_URL}/jobs", params=params, timeout=(5, 12))
            if resp.status_code != 200:
                continue

            vagas.extend(_parse_page(resp.text, seen))

        except Exception as e:
            print(f"[Dribbble] '{query}': {e}")

    print(f"[Dribbble] {len(vagas)} vagas encontradas")
    return vagas
