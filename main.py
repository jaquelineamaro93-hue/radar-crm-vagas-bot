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
    """Coleta única por famílias, persistindo cada fonte logo ao concluir.

    Erros de uma origem nunca descartam vagas já recebidas.
    """
    import inspect
    import os
    from collections import defaultdict, deque
    from search_plan import select_searches

    print("[RADAR] Coleta única iniciada")
    init_db()
    report = report if report is not None else {}
    report.clear()
    report.update({"mode": "unified", "sources": {}, "partial": False,
                   "synced_count": 0, "persistence_errors": 0, "by_category": {}})
    chosen = scrapers if scrapers is not None else ALL_SCRAPERS
    scraped_pool = ThreadPoolExecutor(max_workers=min(8,max(1,len(chosen))))
    sync_pool = ThreadPoolExecutor(max_workers=10)
    scrape_futures = {}
    save_futures = []
    seen_urls = set()
    try:
        for fn in chosen:
            name=fn.__module__.rsplit(".",1)[-1]
            all_terms=fn.__globals__.get("SEARCHES")
            supports_batch="searches" in inspect.signature(fn).parameters
            selected=select_searches(all_terms, source=name,limit=5) if supports_batch and all_terms is not None else None
            report["sources"][name]={"configured_queries":len(all_terms or ()),
                "queries_attempted":len(selected) if selected is not None else None}
            scrape_futures[scraped_pool.submit(_safe_scrape,fn,selected)] = name
        # Close by a bounded deadline; no 25s global timeout for hundreds of queries.
        collect_seconds=min(125,max(35,int(os.getenv("RADAR_COLLECT_TIMEOUT","75"))))
        done,pending=wait(scrape_futures,timeout=collect_seconds)
        for future in done:
            name=scrape_futures[future]
            try:
                jobs=future.result()
                report["sources"][name]["state"]="ok" if jobs else "empty"
                report["sources"][name]["found"]=len(jobs)
            except Exception as e:
                report["sources"][name]["state"]="error"
                report["sources"][name]["error_type"]=type(e).__name__
                print(f"[RADAR] Fonte {name}: {type(e).__name__}")
                continue
            for vaga in jobs:
                if not _passes_location_filter(vaga): continue
                # Catálogo recente: somente datas comprovadas nos últimos 14 dias.
                if not vaga.get("published_at") or not is_recent(vaga["published_at"],days=14): continue
                title=vaga.get("title") or ""
                url=vaga.get("url") or ""
                cat=vaga.get("category") or ""
                if not title or not url or url in seen_urls: continue
                if cat in ("fora_escopo","revisao_escopo","outros",""): continue
                if cat=="designer" and not is_product_design_title(title): continue
                if is_vendas_vaga(vaga) or is_blacklisted(vaga): continue
                seen_urls.add(url)
                report["by_category"][cat]=report["by_category"].get(cat,0)+1
                save_futures.append(sync_pool.submit(_persist_job,vaga))
        for future in pending:
            name=scrape_futures[future]
            report["sources"][name]["state"]="timeout"
            future.cancel()
        report["partial"]=bool(pending) or any(
            x.get("state")=="error" for x in report["sources"].values())
        for future in save_futures:
            try:
                report["synced_count"]+=int(future.result())
            except Exception as e:
                report["persistence_errors"]+=1
                print(f"[RADAR] Persistência: {type(e).__name__}")
        if report["persistence_errors"]:
            raise RuntimeError(f"{report['persistence_errors']} falhas de gravação")
        if not save_futures:
            raise RuntimeError("Nenhuma vaga datada nos últimos 14 dias nas fontes concluídas")
        if not report["synced_count"]:
            raise RuntimeError("Supabase não confirmou sincronização")
        print(f"[RADAR] {report['synced_count']} sincronizadas; parcial={report['partial']}; categorias={report['by_category']}")
        return report["synced_count"]
    finally:
        scraped_pool.shutdown(wait=False,cancel_futures=True)
        sync_pool.shutdown(wait=False,cancel_futures=True)


def _persist_job(vaga):
    # O upsert atualiza metadados por url_hash sem substituir o ID original.
    synced=sync_vaga_crm(vaga)
    if not is_duplicate(vaga["title"],vaga.get("company",""),vaga["url"]):
        if upload_to_supabase(vaga):
            save_vaga(vaga)
    return bool(synced)


def _safe_scrape(fn, searches=None) -> list[dict]:
    try:
        return fn(searches=searches) if searches is not None else fn()
    except Exception as e:
        print(f"[ERRO] {fn.__module__}: {e}")
        return []


if __name__ == "__main__":
    run()
