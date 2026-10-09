import re
import time
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from config import (
    HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, KEYWORDS,
    CXCS_PRIORITY_TERMS, NEW_CXCS_TITLES, CXCS_EXTRA_TITLES_20261001,
)


def fetch(url: str, session: requests.Session = None, extra_headers: dict = None) -> BeautifulSoup | None:
    headers = {**HEADERS, **(extra_headers or {})}
    requester = session or requests
    try:
        resp = requester.get(url, headers=headers, timeout=(5, REQUEST_TIMEOUT))
        resp.raise_for_status()
        time.sleep(REQUEST_DELAY)
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"[ERROR] fetch {url}: {e}")
        return None


def _contains_term(text: str, term: str) -> bool:
    pattern = r"\b" + re.escape(term.casefold()) + r"\b"
    return bool(re.search(pattern, text.casefold()))


_CXCS_EXACT_TITLES = tuple(
    dict.fromkeys(
        title.casefold()
        for title in (NEW_CXCS_TITLES + CXCS_EXTRA_TITLES_20261001)
    )
)


import unicodedata

_PRODUCT_DESIGN_TITLE_RE = re.compile(
    r"\b(?:"
    r"(?:product|ux|ui|ux ui|ui ux|user experience|user interface|service|interaction) design(?:ers?)?"
    r"|design(?:er)? de produto"
    r"|design(?:er)? de servicos"
    r"|design(?:er)? de interacao"
    r"|designer de experiencia do usuario"
    r"|ux researchers?"
    r"|pesquisador(?:a)? de ux"
    r")\b",
    re.IGNORECASE,
)


def is_product_design_title(title: str) -> bool:
    """Reconhece cargos de Product Design / UX / UI pelo titulo, nao por descricao."""
    folded = unicodedata.normalize("NFKD", title or "")
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9]+", " ", folded.casefold()).strip()
    return bool(_PRODUCT_DESIGN_TITLE_RE.search(normalized))


def classify(title: str, description: str = "") -> str | None:
    title_cf = (title or "").casefold()
    text = ((title or "") + " " + (description or "")).casefold()

    # CX/CS precisa ser resolvido antes de CRM. A lista de CRM tem termos
    # sobrepostos (ex.: customer experience, NPS e customer success manager),
    # então o loop genérico fazia vagas de CX/CS caírem na categoria "crm".
    # Títulos exatos enviados pela comunidade têm prioridade máxima.
    if any(exact and exact in title_cf for exact in _CXCS_EXACT_TITLES):
        return "cxcs"

    # Depois priorizamos apenas sinais fortes no TÍTULO, evitando classificar
    # uma vaga de outra área como CX só porque a descrição menciona NPS/CS.
    if any(_contains_term(title_cf, term) for term in CXCS_PRIORITY_TERMS):
        return "cxcs"

    # Product Design nao deve cair em CRM/PO-PM por palavras como product/lead.
    if is_product_design_title(title):
        return "designer"

    for category, keywords in KEYWORDS.items():
        for kw in keywords:
            if _contains_term(text, kw):
                return category
    return None


def is_recent(published_at: str | None, days: int = 30) -> bool:
    """True se a vaga foi publicada nos últimos `days` dias, ou se a data é desconhecida."""
    if not published_at:
        return True
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return dt >= cutoff
    except Exception:
        return True


def format_date(published_at: str | None) -> str:
    """Converte ISO date para texto relativo em PT-BR."""
    if not published_at:
        return "Data não informada"
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        d = delta.days
        if d == 0:
            return "Hoje"
        if d == 1:
            return "Ontem"
        if d < 7:
            return f"Há {d} dias"
        if d < 30:
            w = d // 7
            return f"Há {w} semana{'s' if w > 1 else ''}"
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return published_at


def relative_to_iso(text: str) -> str | None:
    """
    Converte textos relativos do Indeed/LinkedIn (ex: 'há 3 dias', '2 days ago')
    para ISO 8601. Retorna None se não reconhecer.
    """
    import re
    now = datetime.now(timezone.utc)
    text = text.lower().strip()

    patterns = [
        (r"(\d+)\s*dia[s]?\s*atr[aá][s]?|há\s*(\d+)\s*dia", "days"),
        (r"(\d+)\s*days?\s*ago", "days"),
        (r"(\d+)\s*hora[s]?\s*atr[aá][s]?|há\s*(\d+)\s*hora", "hours"),
        (r"(\d+)\s*hours?\s*ago", "hours"),
        (r"(\d+)\s*semana[s]?\s*atr[aá][s]?|há\s*(\d+)\s*semana", "weeks"),
        (r"(\d+)\s*weeks?\s*ago", "weeks"),
        (r"hoje|today|just now|agora", "now"),
        (r"ontem|yesterday", "yesterday"),
        (r"(\d+)\s*m[eê]s|(\d+)\s*month", "months"),
    ]

    for pattern, unit in patterns:
        m = re.search(pattern, text)
        if m:
            if unit == "now":
                return now.isoformat()
            if unit == "yesterday":
                return (now - timedelta(days=1)).isoformat()
            # Pega o primeiro grupo com número
            n = next((int(g) for g in m.groups() if g is not None), 1)
            delta_map = {
                "days": timedelta(days=n),
                "hours": timedelta(hours=n),
                "weeks": timedelta(weeks=n),
                "months": timedelta(days=n * 30),
            }
            return (now - delta_map[unit]).isoformat()

    return None


def extract_seniority(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["junior", "júnior", "jr", "jr.", "trainee", "estágio", "estagio"]):
        return "Junior"
    if any(w in t for w in ["pleno", "mid-level", "mid level", "pl "]):
        return "Pleno"
    if any(w in t for w in ["senior", "sênior", "sénior", "sr", "sr.", "lead", "principal", "staff"]):
        return "Sênior"
    return ""
