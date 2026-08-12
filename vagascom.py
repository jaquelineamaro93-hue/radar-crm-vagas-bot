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
    # ── Designer (remoto) ────────────────────────────────────────────────────
    ("vagas-de-designer",           True,  None),
    ("vagas-de-ux-designer",        True,  None),
    ("vagas-de-product-designer",   True,  None),
    ("vagas-de-web-designer",       True,  None),
    # ── CX / CS (remoto) ────────────────────────────────────────────────────
    ("vagas-de-customer-success",   True,  None),
    ("vagas-de-atendimento-ao-cliente", True, None),
    ("vagas-de-analista-de-suporte", True, None),
    ("vagas-de-customer-experience", True, None),
    # ── Automação Industrial (presencial) ────────────────────────────────────
    ("vagas-de-engenheiro-de-automacao-industrial", False, "automacao_presencial"),
    ("vagas-de-automacao-industrial",               False, "automacao_presencial"),
    ("vagas-de-engenheiro-de-controle",             False, "automacao_presencial"),
    ("vagas-de-instrumentacao-industrial",          False, "automacao_presencial"),
    # ── Projetista de Automação (remoto) ─────────────────────────────────────
    ("vagas-de-projetista-eletrico",     True, "automacao_remote"),
    ("vagas-de-projetista-de-automacao", True, "automacao_remote"),
    ("vagas-de-projetista-de-paineis",   True, "automacao_remote"),
    # ── Dev / Tech Leadership (remoto) ───────────────────────────────────────
    ("vagas-de-tech-lead",                  True, None),
    ("vagas-de-engineering-manager",        True, None),
    ("vagas-de-gerente-de-tecnologia",      True, None),
    ("vagas-de-gerente-de-ti",              True, None),
    ("vagas-de-cto",                        True, None),
    ("vagas-de-desenvolvedor",           True, None),
    ("vagas-de-programador",             True, None),
    ("vagas-de-desenvolvedor-frontend",  True, None),
    ("vagas-de-desenvolvedor-backend",   True, None),
    ("vagas-de-desenvolvedor-fullstack", True, None),
    ("vagas-de-engenheiro-de-software",  True, None),
    # ── Dados (remoto) ───────────────────────────────────────────────────────
    ("vagas-de-analista-de-dados",       True, None),
    ("vagas-de-cientista-de-dados",      True, None),
    ("vagas-de-engenheiro-de-dados",     True, None),
    ("vagas-de-analista-de-business-intelligence", True, None),
    ("vagas-de-machine-learning",        True, None),
    # ── PO / PM (remoto) ─────────────────────────────────────────────────────
    ("vagas-de-product-owner",              True, None),
    ("vagas-de-product-manager",            True, None),
    ("vagas-de-gerente-de-produto",         True, None),
    # ── QA (remoto) ───────────────────────────────────────────────────────────
    ("vagas-de-analista-de-qualidade",      True, None),
    ("vagas-de-analista-de-testes",         True, None),
    ("vagas-de-quality-assurance",          True, None),
    ("vagas-de-qa-analyst",                 True, None),
    # ── CRM (remoto) ─────────────────────────────────────────────────────────
    ("vagas-de-analista-de-crm",   True, None),
    ("vagas-de-analista-de-salesforce", True, None),
    # ── Ed. Física (remoto + presencial SP via filtro em main.py) ─────────────
    ("vagas-de-professor-de-educacao-fisica", False, None),
    ("vagas-de-personal-trainer",            False, None),
    ("vagas-de-preparador-fisico",           False, None),
    ("vagas-de-instrutor-de-academia",       False, None),
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
