"""
Sincronização de vagas CRM com o Supabase.
Salva vagas que pertençam ao ecossistema de CRM/Growth/RevOps/Marketing.
"""
import hashlib
import os
import requests
import re

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

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


def _matches_crm_ecosystem(vaga: dict) -> bool:
    """Verifica se a vaga pertence ao ecossistema de CRM/Growth/Marketing."""
    text_to_search = " ".join([
        vaga.get("title", ""),
        vaga.get("category", ""),
        vaga.get("description", ""),
    ]).lower()

    for keyword in CRM_KEYWORDS:
        if keyword.lower() in text_to_search:
            return True
    return False


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
        "url_hash": _url_hash(vaga["url"]),
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
    except requests.RequestException as e:
        print(f"[WARN] Supabase sync falhou: {e}")
