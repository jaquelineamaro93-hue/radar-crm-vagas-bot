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


def _taxonomia(vaga):
    """Categorias e tags de título; não inferir família a partir de descrições soltas."""
    category=(vaga.get("category") or "").lower()
    title=(vaga.get("title") or "").lower()
    family={"designer":"product-design","ia":"ai","data":"data-analytics",
            "po_pm":"product-management","automacao":"marketing-automation",
            "automacao_presencial":"marketing-automation",
            "automacao_remote":"marketing-automation"}.get(category,category)
    if category=="cxcs":
        family="customer-success" if re.search(r"(customer success|sucesso do cliente|\bcs\b)",title) else "customer-experience"
    tags=[category,family]
    for term,label in (("salesforce","salesforce"),("hubspot","hubspot"),
                       ("marketing cloud","marketing-cloud"),("revops","revops"),
                       ("growth","growth"),("ux","ux"),("e-commerce","ecommerce")):
        if term in title and label not in tags:tags.append(label)
    return family,list(dict.fromkeys(tags))


def _metadata(vaga):
    title=(vaga.get("title") or "")
    description=re.sub(r"\s+"," ",str(vaga.get("description") or "")).strip()
    loc=(vaga.get("location") or "").lower()
    text=" ".join(str(vaga.get(k) or "") for k in ("modality","modality_label","job_type","work_model"))
    combined=(loc+" "+text).lower()
    if re.search(r"(remot|home.?office)",combined):modality="Remoto"
    elif re.search(r"(híbr|hibrid|hybrid)",combined):modality="Híbrido"
    elif re.search(r"(presencial|on.site|onsite)",combined):modality="Presencial"
    else:modality=None
    t=title.lower()
    if re.search(r"(estági|estagi|internship|trainee)",t):seniority="Estágio"
    elif re.search(r"(júnior|junior|\bjr\b)",t):seniority="Júnior"
    elif re.search(r"(\bpleno\b|mid.level)",t):seniority="Pleno"
    elif re.search(r"(sênior|senior|\bsr\b)",t):seniority="Sênior"
    elif re.search(r"(gerente|manager|coordenad|head|lead|diretor)",t):seniority="Liderança"
    else:seniority=None
    contract_text=" ".join(str(vaga.get(k) or "") for k in ("contract","contract_type","job_type","description")).lower()
    contract="CLT" if re.search(r"\bclt\b",contract_text) else "PJ" if re.search(r"\bpj\b",contract_text) else None
    return modality,seniority,description[:500] if description else None,contract


def sync_vaga_crm(vaga: dict):
    if not _configured():
        return
    if not _matches_crm_ecosystem(vaga):
        return
    if not vaga.get("title") or not vaga.get("url"):
        return

    category_slug,tags=_taxonomia(vaga)
    modality,seniority,snippet,contract=_metadata(vaga)
    payload = {
        "categoria_slug": category_slug,
        "tags_correlatas": tags,
        "modalidade_normalizada": modality,
        "senioridade_normalizada": seniority,
        "descricao_resumo": snippet,
        "data_sync": datetime.now(timezone.utc).isoformat(),
        "tipo_contrato": contract,
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
        # O cadastro da vaga não comprova disponibilidade.
        # O banco define 'unverified' para novos registros e preserva o status existente no upsert.
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
