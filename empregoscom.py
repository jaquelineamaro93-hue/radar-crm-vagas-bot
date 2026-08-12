"""
Scraper para Empregos.com.br — board brasileiro de vagas remotas.
Estrutura real (2025):
  div#job-card  → container de cada vaga
    h2.max-w-96 > span  → título
    h3 > a              → empresa
    a[href=/vaga/[id]-[slug]] → link da vaga
Busca na página de home-office e filtra por classify().
"""
import re
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Empregos.com"
BASE_URL = "https://www.empregos.com.br"
HOME_OFFICE_URL = f"{BASE_URL}/vagas/home-office"

MAX_PAGES = 3  # 20 vagas/página × 3 = 60 candidatas


def _parse_page(html: str, seen: set) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    vagas = []

    for card in soup.find_all("div", id="job-card"):
        # Link da vaga
        link_el = card.find("a", href=re.compile(r"^/vaga/\d+"))
        if not link_el:
            continue
        href = link_el.get("href", "")
        url = f"{BASE_URL}{href}" if href.startswith("/") else href
        if url in seen:
            continue

        # Título
        h2 = card.find("h2")
        if not h2:
            continue
        span = h2.find("span")
        title = span.get_text(strip=True) if span else h2.get_text(strip=True)
        if not title:
            continue

        # Empresa
        h3 = card.find("h3")
        company = "Não informado"
        if h3:
            a_comp = h3.find("a")
            company = a_comp.get_text(strip=True) if a_comp else h3.get_text(strip=True)

        category = classify(title)
        if not category:
            continue

        # Data (o site expõe em spans de tempo relativo ou data)
        time_el = card.find("time")
        published_at = time_el.get("datetime") if time_el else None

        seen.add(url)
        vagas.append({
            "title":        title,
            "company":      company or "Não informado",
            "url":          url,
            "location":     "Remoto",
            "description":  "",
            "source":       SOURCE,
            "category":     category,
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

    for page in range(1, MAX_PAGES + 1):
        try:
            params = {"page": page} if page > 1 else {}
            resp = session.get(HOME_OFFICE_URL, params=params, timeout=(5, 12))
            if resp.status_code != 200:
                break
            page_vagas = _parse_page(resp.text, seen)
            vagas.extend(page_vagas)
        except Exception as e:
            print(f"[Empregos.com] página {page}: {e}")
            break

    print(f"[Empregos.com] {len(vagas)} vagas encontradas")
    return vagas
