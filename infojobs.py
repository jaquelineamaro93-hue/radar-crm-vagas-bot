"""
Scraper para InfoJobs.com.br — board com 20 vagas por página.
Requer Accept-Encoding: identity para evitar brotli (não suportado pelo requests).
Datas em formato '2026/04/28 01:53:00' no atributo data-value.
"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from .base import classify

_AUTOMATION_CATS = {"automacao_presencial", "automacao_remote"}
SOURCE = "InfoJobs"
BASE_URL = "https://www.infojobs.com.br"

# (slug, remote_only, forced_category_or_None)
SEARCHES = [
    # CRM genérico
    ("vagas-de-emprego-analista-de-crm-trabalho-home-office",           True, None),
    ("vagas-de-emprego-especialista-em-crm-trabalho-home-office",       True, None),
    ("vagas-de-emprego-coordenador-de-crm-trabalho-home-office",        True, None),
    ("vagas-de-emprego-gerente-de-crm-trabalho-home-office",            True, None),
    ("vagas-de-emprego-diretor-de-crm-trabalho-home-office",            True, None),
    ("vagas-de-emprego-consultor-de-crm-trabalho-home-office",          True, None),
    ("vagas-de-emprego-crm-trabalho-home-office",                       True, None),
    # CRM Marketing
    ("vagas-de-emprego-crm-marketing-trabalho-home-office",             True, None),
    ("vagas-de-emprego-marketing-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-automation-trabalho-home-office",      True, None),
    ("vagas-de-emprego-lifecycle-marketing-trabalho-home-office",       True, None),
    ("vagas-de-emprego-analista-de-campanhas-trabalho-home-office",     True, None),
    # Salesforce
    ("vagas-de-emprego-salesforce-trabalho-home-office",                True, None),
    ("vagas-de-emprego-analista-de-salesforce-trabalho-home-office",    True, None),
    ("vagas-de-emprego-salesforce-developer-trabalho-home-office",      True, None),
    ("vagas-de-emprego-salesforce-administrator-trabalho-home-office",  True, None),
    ("vagas-de-emprego-salesforce-consultant-trabalho-home-office",     True, None),
    ("vagas-de-emprego-marketing-cloud-trabalho-home-office",           True, None),
    # HubSpot
    ("vagas-de-emprego-hubspot-trabalho-home-office",                   True, None),
    ("vagas-de-emprego-analista-de-hubspot-trabalho-home-office",       True, None),
    # RD Station
    ("vagas-de-emprego-rd-station-trabalho-home-office",                True, None),
    # Outras plataformas
    ("vagas-de-emprego-dynamics-crm-trabalho-home-office",              True, None),
    ("vagas-de-emprego-pipedrive-trabalho-home-office",                 True, None),
    ("vagas-de-emprego-activecampaign-trabalho-home-office",            True, None),
    ("vagas-de-emprego-braze-trabalho-home-office",                     True, None),
    ("vagas-de-emprego-klaviyo-trabalho-home-office",                   True, None),
]


def _parse_date(raw: str) -> str | None:
    """Converte '2026/04/28 01:53:00' para ISO 8601."""
    raw = raw.strip()
    try:
        dt = datetime.strptime(raw, "%Y/%m/%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _clean_company(el) -> str:
    """Texto da empresa sem ícones SVG embutidos."""
    if not el:
        return "Não informado"
    for tag in el.find_all(["svg", "i", "span"]):
        tag.decompose()
    return el.get_text(strip=True) or "Não informado"


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen_ids: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
        # identity evita brotli — requests não sabe decodificar br
        "Accept-Encoding": "identity",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    for slug, _remote, forced_cat in SEARCHES:
        url = f"{BASE_URL}/{slug}.aspx"
        try:
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_="js_vacancyLoad")

            for card in cards:
                vaga_id   = card.get("data-id", "")
                data_href = card.get("data-href", "")
                if not vaga_id or vaga_id in seen_ids:
                    continue
                seen_ids.add(vaga_id)

                title_el  = card.find("h2")
                date_el   = card.find("div", class_="js_date")
                comp_link = card.find("a", href=re.compile(r"/empresa-"))
                loc_el    = card.find("div", class_="mb-8")

                title        = title_el.get_text(strip=True) if title_el else ""
                company      = _clean_company(comp_link)
                location     = loc_el.get_text(strip=True) if loc_el else ("Remoto" if _remote else "Presencial")
                raw_date     = (date_el.get("data-value") or "") if date_el else ""
                published_at = _parse_date(raw_date) if raw_date else None
                full_url     = f"{BASE_URL}{data_href}" if data_href else ""

                if not title or not full_url:
                    continue

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
                    "location":     location,
                    "description":  "",
                    "source":       SOURCE,
                    "category":     category,
                    "published_at": published_at,
                })

        except Exception as e:
            print(f"[InfoJobs] {slug}: {e}")

    print(f"[InfoJobs] {len(vagas)} vagas encontradas")
    return vagas
