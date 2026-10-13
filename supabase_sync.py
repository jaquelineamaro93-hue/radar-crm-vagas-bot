"""
Sincronização de vagas CRM com o Supabase.
Salva vagas que pertençam ao ecossistema de CRM/Growth/RevOps/Marketing.
"""
import hashlib
import os
import requests
import re
from datetime import datetime, timezone
from scrapers.base import is_product_design_title

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

# Keywords do ecossistema CRM/Growth/Marketing
CRM_KEYWORDS = [
    "crm",
    "agentes de ia", "ai agents",
    "fde",
    "revops",
    "growth",
    "marketing",
    "salesforce",
    "hubspot",
    "insider",
    "rd station",
    "braze",
    "canais digitais",
    "automacao", "automação",
    "comunicacao", "comunicação",
]


def _configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode()).hexdigest()


# Official job families in the user's catalog. Category is decided by the scraper,
# never inferred from an unrelated job description mentioning a tool.
RADAR_CATEGORIES = frozenset({
    "crm", "cxcs", "designer", "marketing", "revops", "salesops",
    "ia", "data", "po_pm", "qa", "tech", "automacao",
    "automacao_presencial", "automacao_remote",
})


def _matches_crm_ecosystem(vaga: dict) -> bool:
    """Publish all authorized job families equally; no legacy CRM-only gate."""
    category = (vaga.get("category") or "").strip().lower()
    if category not in RADAR_CATEGORIES:
        return False
    if category == "designer":
        return is_product_design_title(vaga.get("title", ""))
    return True


def sync_vaga_crm(vaga: dict):
    if not _configured():
        return
    if not _matches_crm_ecosystem(vaga):
        return
    if not vaga.get("title") or not vaga.get("url"):
        return

    payload = {
        "title": vaga.get("title", "")[:500],
        "company": (vaga.get("company") or "Não informado")[:255],
        "location": (vaga.get("location") or "")[:255],
        "url": vaga.get("url", ""),
        "description": (vaga.get("description") or "")[:2000],
        "source": (vaga.get("source") or "")[:100],
        "published_at": vaga.get("published_at"),
        "category": vaga.get("category"),
        "url_hash": _url_hash(vaga["url"]),
        "last_seen_at": datetime.now(timezone.utc).isoformat(),
        "availability_status": "listed",
        "closure_failures": 0,
    }

    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/vagas_crm",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            params={"on_conflict": "url_hash"},
            json=payload,
            timeout=8,
        )
        if not resp.ok:
            print(f"[WARN] Supabase sync HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.ok
    except requests.RequestException as e:
        print(f"[WARN] Supabase sync falhou: {e}")
        return False
