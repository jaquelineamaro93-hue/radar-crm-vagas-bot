"""
Scraper para Vagas.com.br — maior board de empregos do Brasil.
HTML server-side, sem anti-bot. 40 vagas por página.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from .base import classify

_AUTOMATION_CATS = {"automacao_presencial", "automacao_remote"}
SOURCE = "Vagas.com"
BASE_URL = "https://www.vagas.com.br"

# (slug, remote_only, forced_category_or_None)
# remote_only=True → só aceita vagas com "Home Office" na localização
# forced_category → ignora classify(), usa esta categoria diretamente
SEARCHES = [
    ("vagas-de-crm",                              True, None),
    ("vagas-de-analista-de-crm",                  True, None),
    ("vagas-de-especialista-em-crm",              True, None),
    ("vagas-de-coordenador-de-crm",               True, None),
    ("vagas-de-gerente-de-crm",                   True, None),
    ("vagas-de-diretor-de-crm",                   True, None),
    ("vagas-de-consultor-de-crm",                 True, None),
    ("vagas-de-salesforce",                       True, None),
    ("vagas-de-analista-de-salesforce",           True, None),
    ("vagas-de-salesforce-developer",             True, None),
    ("vagas-de-salesforce-administrator",         True, None),
    ("vagas-de-marketing-cloud",                  True, None),
    ("vagas-de-hubspot",                          True, None),
    ("vagas-de-analista-de-hubspot",              True, None),
    ("vagas-de-rd-station",                       True, None),
    ("vagas-de-crm-marketing",                    True, None),
    ("vagas-de-marketing-de-relacionamento",      True, None),
    ("vagas-de-marketing-automation",             True, None),
    ("vagas-de-analista-de-campanhas",            True, None),
    ("vagas-de-lifecycle-marketing",              True, None),
    ("vagas-de-dynamics-crm",                     True, None),
    ("vagas-de-pipedrive",                        True, None),
    ("vagas-de-braze",                            True, None),
    ("vagas-de-klaviyo",                          True, None),
]


def _parse_date(text: str) -> str | None:
    """Converte '27/04/2026' para ISO 8601."""
    text = text.strip()
    try:
        dt = datetime.strptime(text, "%d/%m/%Y")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _location_text(el) -> str:
    """Extrai texto de localização removendo ícones e tooltips."""
    if not el:
        return ""
    # Remove elementos filhos (ícones, tooltips)
    for child in el.find_all(["i", "div", "span"]):
        child.decompose()
    return el.get_text(strip=True)


def _is_home_office(loc: str) -> bool:
    lower = loc.lower()
    return any(w in lower for w in ["home office", "remoto", "trabalho remoto", "remote"])


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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    for slug, remote_only, forced_cat in SEARCHES:
        url = f"{BASE_URL}/{slug}"
        if remote_only:
            url += "?homeoffice=1"
        try:
            resp = session.get(url, timeout=(5, 10))
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("li.vaga"):
                link_el  = card.select_one("a.link-detalhes-vaga")
                comp_el  = card.select_one("span.emprVaga")
                loc_el   = card.select_one(".vaga-local")
                date_el  = card.select_one("span.data-publicacao")

                if not link_el:
                    continue

                href = link_el.get("href", "")
                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                title    = link_el.get("title") or link_el.get_text(strip=True)
                company  = comp_el.get_text(strip=True) if comp_el else "Não informado"
                location = _location_text(loc_el) if loc_el else ""

                # Para buscas remotas: pula vagas presenciais (cidade sem "Home Office")
                if remote_only and not _is_home_office(location):
                    continue

                raw_date = ""
                if date_el:
                    for child in date_el.find_all("i"):
                        child.decompose()
                    raw_date = date_el.get_text(strip=True)
                published_at = _parse_date(raw_date) if raw_date else None

                if forced_cat:
                    # Para categorias de automação, valida o título mesmo com forced_cat
                    if forced_cat in _AUTOMATION_CATS and classify(title) not in _AUTOMATION_CATS:
                        continue
                    category = forced_cat
                else:
                    category = classify(title)
                    if not category:
                        continue

                vagas.append({
                    "title":        title,
                    "company":      company,
                    "url":          full_url,
                    "location":     location or ("Remoto" if remote_only else "Presencial"),
                    "description":  "",
                    "source":       SOURCE,
                    "category":     category,
                    "published_at": published_at,
                })

        except Exception as e:
            print(f"[Vagas.com] {slug}: {e}")

    print(f"[Vagas.com] {len(vagas)} vagas encontradas")
    return vagas
