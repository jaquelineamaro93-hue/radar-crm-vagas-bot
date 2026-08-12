"""
Scraper para Programathor.com.br — board de tech do Brasil.
Estrutura real da página:
  <a href="/jobs/[id]-[slug]">
    <div class="cell-list">
      <div class="row">
        <div class="col-sm-3"> (logo) </div>
        <div class="col-sm-9">
          <div class="cell-list-content">
            <h3 class="text-24">Título<span class="new-label">NOVA</span></h3>
            <div class="cell-list-content-icon">
              <span>Empresa</span>
              <span>Localização</span>
              ...
            </div>
          </div>
        </div>
      </div>
    </div>
  </a>
Filtra apenas vagas remotas por categoria.
"""
import re
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Programathor"
BASE_URL = "https://programathor.com.br"
LIST_URL = f"{BASE_URL}/jobs"

# Palavras que indicam vaga remota
_REMOTE_WORDS = {"remoto", "remote", "home office", "ho", "100% remoto"}

# Páginas a percorrer — cada página tem ~15 vagas
MAX_PAGES = 4


def _is_remote(location: str) -> bool:
    loc = location.lower()
    return any(w in loc for w in _REMOTE_WORDS)


def _parse_page(html: str, seen: set) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    vagas = []

    # Cada vaga é um <a href="/jobs/[id]-[slug]"> que contém div.cell-list
    for a in soup.find_all("a", href=re.compile(r"^/jobs/\d+")):
        href = a.get("href", "")
        url = f"{BASE_URL}{href}"
        if url in seen:
            continue

        cell = a.find("div", class_="cell-list-content")
        if not cell:
            continue

        # Título — remove span.new-label ("NOVA")
        h3 = cell.find("h3", class_="text-24")
        if not h3:
            continue
        for span in h3.find_all("span", class_="new-label"):
            span.decompose()
        title = h3.get_text(strip=True)
        if not title:
            continue

        # Empresa e localização (spans dentro de cell-list-content-icon)
        icon_div = cell.find("div", class_="cell-list-content-icon")
        spans = icon_div.find_all("span") if icon_div else []
        # Extrai texto de cada span removendo ícones fa
        def _span_text(sp):
            for i in sp.find_all(["i", "svg"]):
                i.decompose()
            return sp.get_text(strip=True)

        company  = _span_text(spans[0]) if spans else "Não informado"
        location = _span_text(spans[1]) if len(spans) > 1 else ""

        # Filtra vagas não-remotas
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
            "published_at": None,  # Programathor não expõe data na listagem
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
            resp = session.get(LIST_URL, params=params, timeout=(5, 12))
            if resp.status_code != 200:
                break

            page_vagas = _parse_page(resp.text, seen)
            vagas.extend(page_vagas)

            # Se não encontrou vagas novas nesta página, para
            if not page_vagas and page > 1:
                break

        except Exception as e:
            print(f"[Programathor] página {page}: {e}")
            break

    print(f"[Programathor] {len(vagas)} vagas encontradas")
    return vagas
