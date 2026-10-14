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
from scrapers.base import is_recent, is_product_design_title, classify

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


def run(scrapers: list | None = None, report: dict | None = None) -> int:
    """Um único ciclo com todas as famílias, buscas equilibradas e diagnóstico.

    Fontes sem resposta não bloqueiam a gravação das fontes concluídas.
    Não apaga vagas nem separa CRM de Product Design em crons diferentes.
    """
    import inspect
    import os
    from collections import defaultdict, deque
    from search_plan import select_searches

    print("=" * 50)
    print("[RADAR] Coleta unificada iniciada")
    init_db()
    report = report if report is not None else {}
    report.clear()
    report.update({"mode": "unified", "sources": {}, "partial": False})

    tasks = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fn in (scrapers if scrapers is not None else ALL_SCRAPERS):
            name = fn.__module__.rsplit(".",1)[-1]
            all_terms = fn.__globals__.get("SEARCHES")
            supports_batch = "searches" in inspect.signature(fn).parameters
            selected = select_searches(all_terms, source=name, limit=16) if supports_batch and all_terms is not None else None
            report["sources"][name] = {"configured_queries": len(all_terms or ()),
                                       "queries_attempted": len(selected) if selected is not None else None}
            tasks[pool.submit(_safe_scrape, fn, selected)] = name
        # Full scans of hundreds of serial searches never finished within 25s.
        # The bounded batch above allows the job to finish on Vercel Fluid Compute.
        timeout = min(235, max(40, int(os.getenv("RADAR_COLLECT_TIMEOUT", "175"))))
        completed, pending = wait(tasks,timeout=timeout)
        all_vagas = []
        for future in completed:
            name=tasks[future]
            try:
                found=future.result()
                all_vagas.extend(found)
                report["sources"][name]["found"] = len(found)
                report["sources"][name]["state"] = "ok" if found else "empty"
            except Exception as exc:
                report["sources"][name]["state"] = "error"
                report["sources"][name]["error_type"] = type(exc).__name__
                print(f"[RADAR] Fonte {name} falhou: {type(exc).__name__}")
        for future in pending:
            name=tasks[future]
            report["sources"][name]["state"] = "timeout"
            future.cancel()
        report["partial"] = bool(pending)
        report["raw_count"] = len(all_vagas)
        # Do not wait for long-running requests after the deadline.
        pool.shutdown(wait=False, cancel_futures=True)
    print(f"[RADAR] Fontes concluídas: {len(completed)}/{len(tasks)}; coletadas: {len(all_vagas)}")

    filtered=[v for v in all_vagas if _passes_location_filter(v) and is_recent(v.get("published_at"),days=60)]
    groups=defaultdict(deque)
    seen_urls=set()
    for vaga in filtered:
        title=vaga.get("title") or ""
        url=vaga.get("url") or ""
        category=vaga.get("category")
        if not title or not url:continue
        if category=="designer" and not is_product_design_title(title):continue
        if category in ("fora_escopo","revisao_escopo","outros") or not category:continue
        if is_vendas_vaga(vaga) or is_blacklisted(vaga):continue
        if url in seen_urls:continue
        seen_urls.add(url)
        groups[category].append(vaga)
    queue=[]
    while any(groups.values()):
        for category in sorted(groups):
            if groups[category]:
                queue.append(groups[category].popleft())
    report["valid_count"]=len(queue)
    category_counts={}
    for job in queue:
        category=job.get("category","outros")
        category_counts[category]=category_counts.get(category,0)+1
    report["by_category"]=category_counts

    def persist(vaga):
        synced=sync_vaga_crm(vaga)
        if not is_duplicate(vaga["title"],vaga.get("company",""),vaga["url"]):
            if upload_to_supabase(vaga):
                save_vaga(vaga)
        return bool(synced)

    synced_total=0
    errors=0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures=[pool.submit(persist,v) for v in queue]
        for future in futures:
            try:
                synced_total+=int(future.result())
            except Exception as exc:
                errors+=1
                print(f"[RADAR] Falha ao persistir: {type(exc).__name__}")
    report["synced_count"]=synced_total
    report["persistence_errors"]=errors
    if errors:
        raise RuntimeError(f"{errors} erros de gravação; sincronizadas={synced_total}")
    if not queue:
        raise RuntimeError("Nenhuma vaga elegível coletada; revisar fontes, bloqueios e buscas")
    if synced_total == 0:
        raise RuntimeError("Nenhuma vaga sincronizada; revisar permissões e retorno do Supabase")
    print(f"[RADAR] Sincronizadas: {synced_total}; categorias: {category_counts}; parcial: {report['partial']}")
    return synced_total


def _safe_scrape(fn, searches=None) -> list[dict]:
    try:
        return fn(searches=searches) if searches is not None else fn()
    except Exception as e:
        print(f"[ERRO] {fn.__module__}: {e}")
        return []


if __name__ == "__main__":
    run()
