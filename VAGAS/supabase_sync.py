"""
Sincronização das vagas de categoria "crm" com o Supabase, para
alimentar a aba "Vagas de CRM" do Radar CRM (dashboard da comunidade).

Usa a REST API do Supabase diretamente via requests, sem dependência
extra no requirements.txt. Falha de forma silenciosa (só loga o erro)
para nunca travar o fluxo principal do bot (Discord continua funcionando
mesmo se o Supabase estiver fora do ar).

Variáveis de ambiente necessárias (mesmas do resto do projeto Radar CRM):
  SUPABASE_URL           ex: https://rwkbpafpniwzvlkfngag.supabase.co
  SUPABASE_ANON_KEY       chave publishable/anon do projeto
"""
import hashlib
import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode()).hexdigest()


def sync_vaga_crm(vaga: dict):
    """Envia uma vaga da categoria 'crm' para a tabela vagas_crm no Supabase.
    Usa upsert por url_hash para nunca duplicar a mesma vaga."""
    if not _configured():
        return
    if vaga.get("category") != "crm":
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
            print(f"[WARN] Supabase sync (vagas_crm) HTTP {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as e:
        print(f"[WARN] Supabase sync (vagas_crm) falhou: {e}")
