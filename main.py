"""
Orquestrador principal.
Roda os scrapers em paralelo para caber no timeout de 60s do Vercel.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from database import init_db, is_duplicate, save_vaga, upload_to_supabase, is_vendas_vaga, is_blacklisted
# Notifier removido
from supabase_sync import sync_vaga_crm
from scrapers import ALL_SCRAPERS
from scrapers.base import is_recent, is_product_design_title

# Palavras que indicam vaga presencial — descarta para categorias remotas
_PRESENCIAL = {"presencial", "on-site", "onsite", "in-office", "híbrido", "hibrido", "hybrid"}


def _is_remote(vaga: dict) -> bool:
    loc = vaga.get("location", "").lower()
    return not any(w in loc for w in _PRESENCIAL)


def _is_sao_paulo(vaga: dict) -> bool:
    loc = vaga.get("location", "").lower()
    return ("são paulo" in loc or "sao paulo" in loc or
            bool(re.search(r"\bsp\b", loc)))


def _passes_location_filter(vaga: dict) -> bool:
    cat = vaga.get("category", "")
    # Automação: localização já pré-filtrada no scraper (on-site ou remote)
    if cat in ("automacao_presencial", "automacao_remote"):
        return True
    # Product Design: incluir remoto, hibrido e presencial no Brasil.
    if cat == "designer" and is_product_design_title(vaga.get("title", "")):
        return True
    return True  # Preserve on-site/hybrid roles for dashboard filtering


def run(scrapers: list | None = None) -> int:
    print("=" * 50)
    print("Iniciando coleta de vagas...")

    # Debug: verificar qual chave está sendo usada
    import os
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    anon_key = os.getenv("SUPABASE_ANON_KEY", "")
    print(f"[DEBUG] SERVICE_ROLE_KEY presente: {bool(service_key)} (len={len(service_key) if service_key else 0})")
    print(f"[DEBUG] ANON_KEY presente: {bool(anon_key)} (len={len(anon_key) if anon_key else 0})")
    print(f"[DEBUG] Será usado: {'SERVICE_ROLE' if service_key else 'ANON'}")

    init_db()

    # Vercel Hobby functions have a bounded execution window. Never wait
    # 120s for scrapers before beginning database writes.
    all_vagas: list[dict] = []
    executor = ThreadPoolExecutor(max_workers=12)
    try:
        futures = {executor.submit(_safe_scrape, fn): fn.__module__
                   for fn in (scrapers if scrapers is not None else ALL_SCRAPERS)}
        completed, pending = wait(futures, timeout=25)
        for future in completed:
            try:
                all_vagas.extend(future.result())
            except Exception as e:
                print(f"[WARN] Fonte indisponivel: {e}")
        print(f"[INFO] Fontes concluidas: {len(completed)}/{len(futures)}; pendentes: {len(pending)}")
        if pending:
            print(f"[ERROR] {len(pending)} fontes excederam o prazo de coleta")
            # Persist successful sources first; never discard collected vacancies.
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    print(f"[DEBUG] Total coletado: {len(all_vagas)} vagas")

    # Filtra: localização válida por categoria + publicadas no período por categoria
    # CRM: 60 dias (populate inicial); demais: 30 dias
    def _days_for(vaga: dict) -> int:
        return 60 if vaga.get("category") in ("crm", "data", "po_pm", "qa") else 30

    # Debug filtros individuais
    location_ok = [v for v in all_vagas if _passes_location_filter(v)]
    print(f"[DEBUG] Após filtro localização: {len(location_ok)}")

    recent_ok = [v for v in location_ok if is_recent(v.get("published_at"), days=_days_for(v))]
    print(f"[DEBUG] Após filtro data: {len(recent_ok)}")

    filtradas = recent_ok
    print(f"[DEBUG] Total após filtros: {len(filtradas)}")

    # Keep a bounded workload, interleaving categories so none is preferred.
    from collections import defaultdict, deque
    groups = defaultdict(deque)
    seen_urls = set()
    for vaga in filtradas:
        if not vaga.get("title") or not vaga.get("url"):
            continue
        if is_vendas_vaga(vaga) or is_blacklisted(vaga):
            continue
        if vaga["url"] in seen_urls:
            continue
        seen_urls.add(vaga["url"])
        groups[vaga.get("category") or "outros"].append(vaga)
    queue = []
    while any(groups.values()):
        for category in sorted(groups):
            if groups[category]:
                queue.append(groups[category].popleft())

    def persist(vaga):
        # Upsert into the public catalog even if the job is already in the
        # local dedup cache; this updates last_seen_at without deleting history.
        synced = sync_vaga_crm(vaga)
        if not is_duplicate(vaga["title"], vaga.get("company", ""), vaga["url"]):
            if upload_to_supabase(vaga):
                save_vaga(vaga)
        return bool(synced)

    total_novas = 0
    erros = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        jobs = [pool.submit(persist, vaga) for vaga in queue]
        for future in jobs:
            try:
                total_novas += int(future.result())
            except Exception as e:
                print(f"[ERRO] Falha ao sincronizar vaga: {e}")
                erros += 1
    print(f"[INFO] Processadas {len(queue)} vagas de {len(groups)} categorias")

    print(f"Vagas sincronizadas: {total_novas} | Erros: {erros}")
    if erros or pending:
        raise RuntimeError(f"Coleta parcial: {len(pending)} fontes pendentes, {erros} falhas de persistencia; {total_novas} vagas sincronizadas")
    print("=" * 50)
    return total_novas


def _safe_scrape(fn) -> list[dict]:
    try:
        return fn()
    except Exception as e:
        print(f"[ERRO] {fn.__module__}: {e}")
        return []


if __name__ == "__main__":
    run()
