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
    # ── Designer (remoto) ────────────────────────────────────────────────────
    ("vagas-de-emprego-designer-trabalho-home-office",          True,  None),
    ("vagas-de-emprego-ux-designer-trabalho-home-office",       True,  None),
    ("vagas-de-emprego-product-designer-trabalho-home-office",  True,  None),
    # ── CX / CS (remoto) ────────────────────────────────────────────────────
    ("vagas-de-emprego-customer-success-trabalho-home-office",  True,  None),
    ("vagas-de-emprego-customer-experience-trabalho-home-office", True, None),
    ("vagas-de-emprego-atendimento-ao-cliente-trabalho-home-office", True, None),
    # ── Automação Industrial (presencial) ────────────────────────────────────
    ("vagas-de-emprego-engenheiro-de-automacao-industrial",     False, "automacao_presencial"),
    ("vagas-de-emprego-automacao-industrial",                   False, "automacao_presencial"),
    ("vagas-de-emprego-programador-clp",                        False, "automacao_presencial"),
    # ── Projetista de Automação (remoto) ─────────────────────────────────────
    ("vagas-de-emprego-projetista-eletrico-trabalho-home-office",    True, "automacao_remote"),
    ("vagas-de-emprego-projetista-de-automacao-trabalho-home-office", True, "automacao_remote"),
    # ── Dev / Tech Leadership (remoto) ───────────────────────────────────────
    ("vagas-de-emprego-tech-lead-trabalho-home-office",                  True, None),
    ("vagas-de-emprego-gerente-de-tecnologia-trabalho-home-office",      True, None),
    ("vagas-de-emprego-gerente-de-ti-trabalho-home-office",              True, None),
    ("vagas-de-emprego-engineering-manager-trabalho-home-office",        True, None),
    ("vagas-de-emprego-desenvolvedor-trabalho-home-office",          True, None),
    ("vagas-de-emprego-programador-trabalho-home-office",            True, None),
    ("vagas-de-emprego-desenvolvedor-web-trabalho-home-office",      True, None),
    ("vagas-de-emprego-desenvolvedor-fullstack-trabalho-home-office", True, None),
    # ── Dados (remoto) ───────────────────────────────────────────────────────
    ("vagas-de-emprego-analista-de-dados-trabalho-home-office",      True, None),
    ("vagas-de-emprego-cientista-de-dados-trabalho-home-office",     True, None),
    ("vagas-de-emprego-engenheiro-de-dados-trabalho-home-office",    True, None),
    ("vagas-de-emprego-analista-de-business-intelligence-trabalho-home-office", True, None),
    # ── PO / PM (remoto) ─────────────────────────────────────────────────────
    ("vagas-de-emprego-product-owner-trabalho-home-office",              True, None),
    ("vagas-de-emprego-product-manager-trabalho-home-office",            True, None),
    ("vagas-de-emprego-gerente-de-produto-trabalho-home-office",         True, None),
    # ── QA (remoto) ───────────────────────────────────────────────────────────
    ("vagas-de-emprego-analista-de-qualidade-trabalho-home-office",      True, None),
    ("vagas-de-emprego-analista-de-testes-trabalho-home-office",         True, None),
    ("vagas-de-emprego-quality-assurance-trabalho-home-office",          True, None),
    # ── CRM (remoto) ─────────────────────────────────────────────────────────
    ("vagas-de-emprego-analista-de-crm-trabalho-home-office",        True, None),
    ("vagas-de-emprego-analista-de-salesforce-trabalho-home-office", True, None),
    # ── Ed. Física (presencial + remoto — filtro por SP em main.py) ──────────
    ("vagas-de-emprego-professor-de-educacao-fisica",                False, None),
    ("vagas-de-emprego-personal-trainer",                            False, None),
    ("vagas-de-emprego-preparador-fisico",                           False, None),
    ("vagas-de-emprego-professor-de-educacao-fisica-trabalho-home-office", True, None),
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
