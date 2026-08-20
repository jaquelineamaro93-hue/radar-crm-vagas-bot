"""
Scraper para Nerdin.com.br — board de vagas de TI no Brasil.
Estrutura real (2025):
  <div class="vaga-card" onclick="...window.location.href='vaga_emprego/vaga-[slug].php'">
    <h3 class="vaga-titulo">Título<span class="vaga-nova-badge">NEW</span></h3>
    <div class="vaga-empresa"><i>...icon...</i>  Nome da Empresa </div>
    <div class="vaga-local"><i>...icon...</i>  Localização</div>
  </div>

Usa /vagas-home-office.php para filtrar vagas remotas.
"""
import re
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Nerdin"
BASE_URL = "https://nerdin.com.br"

# Nerdin tem uma página dedicada a Home Office
REMOTE_URL = f"{BASE_URL}/vagas-home-office.php"
GENERAL_URL = f"{BASE_URL}/vagas.php"

# Palavras que indicam vaga remota
_REMOTE_WORDS = {"home office", "ho", "remoto", "remote", "100% remoto", "trabalho remoto"}
MAX_PAGES = 4

CRM_SEARCHES = [
    f"{BASE_URL}/vagas.php?q=crm",
    f"{BASE_URL}/vagas.php?q=salesforce",
    f"{BASE_URL}/vagas.php?q=hubspot",
    f"{BASE_URL}/vagas.php?q=rd+station",
    f"{BASE_URL}/vagas.php?q=marketing+relacionamento",
    f"{BASE_URL}/vagas.php?q=crm+marketing",
    f"{BASE_URL}/vagas.php?q=braze",
    f"{BASE_URL}/vagas.php?q=klaviyo",
    f"{BASE_URL}/vagas.php?q=pipedrive",
    f"{BASE_URL}/vagas.php?q=marketing+automation",
]



def _is_remote(loc: str) -> bool:
    lower = loc.lower()
    return any(w in lower for w in _REMOTE_WORDS)


def _extract_url_from_onclick(onclick: str) -> str:
    """Extrai 'vaga_emprego/vaga-xxx.php' do atributo onclick do div.vaga-card."""
    m = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick or "")
    return m.group(1) if m else ""


def _clean_text(el) -> str:
    """Remove ícones fa/svg e retorna texto limpo."""
    if not el:
        return ""
    for tag in list(el.find_all(["i", "svg", "span"])):
        # Guarda contra tags com attrs=None (HTML malformado)
        try:
            cls = tag.attrs.get("class", []) if tag.attrs else []
        except AttributeError:
            cls = []
        if tag.name in ("i", "svg") or any("badge" in c or "selo" in c or "stack" in c for c in cls):
            tag.decompose()
    return el.get_text(strip=True) or ""


def _parse_page(html: str, seen: set) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    vagas = []

    for card in soup.find_all("div", class_="vaga-card"):
        onclick = card.get("onclick", "")
        rel_href = _extract_url_from_onclick(onclick)
        if not rel_href:
            # Fallback: botão btn-ver-vaga
            btn = card.find("a", class_="btn-ver-vaga")
            rel_href = btn.get("href", "") if btn else ""

        if not rel_href:
            continue

        full_url = f"{BASE_URL}/{rel_href}" if not rel_href.startswith("http") else rel_href
        if full_url in seen:
            continue

        # Título — remove badge "NEW"
        h3 = card.find("h3", class_="vaga-titulo")
        if not h3:
            continue
        for badge in h3.find_all("span"):
            badge.decompose()
        title = h3.get_text(strip=True)
        if not title:
            continue

        # Empresa
        emp_el = card.find("div", class_="vaga-empresa")
        company = _clean_text(emp_el) or "Não informado"

        # Localização
        loc_el = card.find("div", class_="vaga-local")
        location = _clean_text(loc_el) or ""

        category = classify(title)
        if not category:
            continue

        seen.add(full_url)
        vagas.append({
            "title":        title,
            "company":      company,
            "url":          full_url,
            "location":     location or "Remoto",
            "description":  "",
            "source":       SOURCE,
            "category":     category,
            "published_at": None,
        })

    return vagas


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for url in CRM_SEARCHES:
        try:
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code == 200:
                vagas.extend(_parse_page(resp.text, seen))
        except Exception as e:
            print(f"[Nerdin] Erro '{url}': {e}")

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

    # Página dedicada de home office (vagas remotas)
    for page in range(1, MAX_PAGES + 1):
        try:
            params = {"pagina": page} if page > 1 else {}
            resp = session.get(REMOTE_URL, params=params, timeout=(5, 12))
            if resp.status_code != 200:
                break
            page_vagas = _parse_page(resp.text, seen)
            vagas.extend(page_vagas)
            if not page_vagas and page > 1:
                break
        except Exception as e:
            print(f"[Nerdin] home-office página {page}: {e}")
            break

    # Página geral — filtra por localização remota
    # (captura vagas remotas que possam não estar na página de HO)
    try:
        resp = session.get(GENERAL_URL, timeout=(5, 12))
        if resp.status_code == 200:
            all_vagas = _parse_page(resp.text, seen)
            remote_vagas = [v for v in all_vagas if _is_remote(v.get("location", ""))]
            vagas.extend(remote_vagas)
    except Exception as e:
        print(f"[Nerdin] geral: {e}")

    print(f"[Nerdin] {len(vagas)} vagas encontradas")
    return vagas
