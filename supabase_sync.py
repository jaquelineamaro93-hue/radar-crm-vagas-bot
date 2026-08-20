import hashlib, os, requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

def sync_vaga_crm(vaga: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    if not vaga.get("title") or not vaga.get("url"):
        return
    payload = {
        "title": vaga.get("title","")[:500],
        "company": (vaga.get("company") or "Não informado")[:255],
        "location": (vaga.get("location") or "")[:255],
        "url": vaga.get("url",""),
        "description": (vaga.get("description") or "")[:2000],
        "source": (vaga.get("source") or "")[:100],
        "published_at": vaga.get("published_at"),
        "url_hash": hashlib.sha256(vaga["url"].strip().encode()).hexdigest(),
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
            print(f"[WARN] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[WARN] Falhou: {e}")
