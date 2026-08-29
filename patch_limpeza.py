"""
Adiciona ao app.py:
1. Função cleanup_vagas_fechadas() — verifica cada vaga e remove do Supabase se URL retornar 404/403/410
2. Chama cleanup junto com o scrape diário no /api/scrape
"""

CLEANUP_CODE = '''

def cleanup_vagas_fechadas():
    """Remove do Supabase vagas cujas URLs retornam 404/403/410 (vagas fechadas)."""
    import requests as _req
    import os as _os

    SUPABASE_URL = _os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_KEY = _os.environ.get("SUPABASE_ANON_KEY", "")
    if not SUPABASE_URL or not SUPABASE_KEY:
        return 0

    headers_sb = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    headers_req = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    }

    # Buscar vagas mais antigas que 7 dias (as recentes provavelmente ainda estão abertas)
    resp = _req.get(
        f"{SUPABASE_URL}/rest/v1/vagas_crm",
        headers=headers_sb,
        params={
            "select": "id,url,title",
            "found_at": f"lt.{__import__('datetime').datetime.utcnow().replace(microsecond=0).isoformat()}",
            "limit": "200",
            "order": "found_at.asc",
        },
        timeout=10,
    )
    if not resp.ok:
        print(f"[cleanup] Erro ao buscar vagas: {resp.status_code}")
        return 0

    vagas = resp.json()
    removidas = 0

    for vaga in vagas:
        url = vaga.get("url", "")
        vaga_id = vaga.get("id")
        if not url or not vaga_id:
            continue
        try:
            r = _req.head(url, headers=headers_req, timeout=6, allow_redirects=True)
            if r.status_code in (404, 410, 403, 400):
                # Deletar do Supabase
                del_resp = _req.delete(
                    f"{SUPABASE_URL}/rest/v1/vagas_crm",
                    headers=headers_sb,
                    params={"id": f"eq.{vaga_id}"},
                    timeout=8,
                )
                if del_resp.ok:
                    removidas += 1
                    print(f"[cleanup] Removida vaga fechada: {vaga.get('title','?')[:50]}")
        except Exception:
            pass  # timeout ou erro de rede — manter a vaga

    print(f"[cleanup] {removidas} vagas fechadas removidas de {len(vagas)} verificadas")
    return removidas
'''

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

if "def cleanup_vagas_fechadas" in content:
    print("AVISO: cleanup já existe no app.py")
else:
    # Inserir a função antes do bloco de match
    content = content.replace(
        "# ============ MATCH POR IA",
        CLEANUP_CODE + "\n# ============ MATCH POR IA"
    )

    # Atualizar /api/scrape para chamar cleanup também
    content = content.replace(
        '''    try:
        from main import run
        count = run()
        return jsonify({"status": "ok", "novas_vagas": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500''',
        '''    try:
        from main import run
        count = run()
        removidas = cleanup_vagas_fechadas()
        return jsonify({"status": "ok", "novas_vagas": count, "vagas_removidas": removidas})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500'''
    )

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("OK: cleanup_vagas_fechadas adicionado ao app.py")
    print("OK: /api/scrape agora chama cleanup após coletar vagas")
