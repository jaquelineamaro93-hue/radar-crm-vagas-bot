"""
Scraper para Indeed Brasil (br.indeed.com).
Os dados de vagas ficam em window.mosaic.providerData["mosaic-provider-jobcards"]
no HTML — não precisa de JS. Estratégia: keyword + "remoto" para garantir
que o Indeed filtre por vagas remotas.

URL: https://br.indeed.com/jobs?q={keyword}&fromage={days}
     (fromage = dias desde a publicação)

Cada busca retorna ~15 vagas. Pulamos respostas < 100KB (CAPTCHA/bloqueio).
"""
import re
import json
import time
import requests
from datetime import datetime, timezone
from .base import classify

SOURCE = "Indeed"
BASE_URL = "https://br.indeed.com"
SEARCH_URL = f"{BASE_URL}/jobs"

# (query, fromage_days)
# O termo "remoto" faz parte do keyword para pré-filtrar no Indeed
SEARCHES = [
    ("crm",                          30),
    ("analista de crm",              30),
    ("especialista crm",             30),
    ("gerente crm",                  30),
    ("diretor crm",                  30),
    ("salesforce",                   30),
    ("salesforce developer",         30),
    ("salesforce administrator",     30),
    ("marketing cloud",              30),
    ("hubspot",                      30),
    ("rd station",                   30),
    ("crm marketing",                30),
    ("marketing de relacionamento",  30),
    ("marketing automation",         30),
    ("analista de campanhas",        30),
    ("dynamics crm",                 30),
    ("pipedrive",                    30),
    ("braze",                        30),
    ("klaviyo",                      30),
    ("lifecycle marketing",          30),
    ("jornada do cliente",           30),
]

_REMOTE_WORDS = {"remoto", "remote", "home office", "trabalho remoto"}
# Respostas menores que esse tamanho são CAPTCHA / página de bloqueio
_MIN_HTML_SIZE = 100_000


def _is_remote(loc: str) -> bool:
    lower = loc.lower()
    return any(w in lower for w in _REMOTE_WORDS)


def _parse_mosaic(html: str) -> list[dict]:
    """Extrai vagas do JSON mosaic embutido no HTML do Indeed."""
    m = re.search(
        r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.+?\});\s*window\.mosaic',
        html,
        re.DOTALL,
    )
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
        return (
            data.get("metaData", {})
                .get("mosaicProviderJobCardsModel", {})
                .get("results", [])
        )
    except (json.JSONDecodeError, AttributeError):
        return []


def _result_to_vaga(r: dict) -> dict | None:
    jk = r.get("jobkey", "")
    if not jk:
        return None

    title = r.get("displayTitle") or r.get("title", "")
    if not title:
        return None

    company  = r.get("company") or "Não informado"
    location = r.get("formattedLocation") or ""

    if not _is_remote(location):
        return None

    category = classify(title)
    if not category:
        return None

    url = f"{BASE_URL}/ver-vaga?jk={jk}"

    # pubDate = Unix timestamp em milissegundos
    pub_ms = r.get("pubDate")
    published_at = None
    if pub_ms:
        try:
            dt = datetime.fromtimestamp(pub_ms / 1000, tz=timezone.utc)
            published_at = dt.isoformat()
        except (OSError, ValueError):
            pass

    return {
        "title":        title,
        "company":      company,
        "url":          url,
        "location":     location,
        "description":  "",
        "source":       SOURCE,
        "category":     category,
        "published_at": published_at,
    }


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen_jks: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": BASE_URL,
    })

    for query, fromage in SEARCHES:
        try:
            resp = session.get(
                SEARCH_URL,
                params={"q": query, "fromage": fromage},
                timeout=(5, 12),
            )
            if resp.status_code != 200:
                continue

            # Resposta curta = CAPTCHA / bloqueio do Indeed
            if len(resp.text) < _MIN_HTML_SIZE:
                continue

            for r in _parse_mosaic(resp.text):
                jk = r.get("jobkey", "")
                if jk in seen_jks:
                    continue
                seen_jks.add(jk)
                vaga = _result_to_vaga(r)
                if vaga:
                    vagas.append(vaga)

            time.sleep(0.3)

        except Exception as e:
            print(f"[Indeed] '{query}': {e}")

    print(f"[Indeed] {len(vagas)} vagas encontradas")
    return vagas
