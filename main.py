"""
Orquestrador principal.
Roda os scrapers em paralelo para caber no timeout de 60s do Vercel.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
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
    from search_plan import select_search_batch

    print("[RADAR] Coleta única iniciada")
    init_db()
    report = report if report is not None else {}
    report.clear()
    report.update({"mode": "unified", "sources": {}, "partial": False,
                   "synced_count": 0, "persistence_errors": 0, "by_category": {},
                   "discarded_missing_date": 0, "discarded_old_date": 0,
                   "discarded_out_of_scope": 0})
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
            selected, progress = select_search_batch(all_terms, source=name) if supports_batch and all_terms is not None else (None, {})
            report["sources"][name]={"configured_queries":len(all_terms or ()),
                "queries_attempted":len(selected) if selected is not None else len(all_terms or ()),
                "cursor": progress}
            scrape_futures[scraped_pool.submit(_safe_scrape,fn,selected)] = name
        # Close by a bounded deadline; no 25s global timeout for hundreds of queries.
        collect_seconds=min(125,max(35,int(os.getenv("RADAR_COLLECT_TIMEOUT","75"))))
        completed=set()
        try:
            futures_to_iterate=as_completed(scrape_futures,timeout=collect_seconds)
            for future in futures_to_iterate:
                completed.add(future)
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
                    if not _passes_location_filter(vaga):
                        report["discarded_out_of_scope"] += 1
                        continue
                    published = vaga.get("published_at")
                    if not published:
                        report["discarded_missing_date"] += 1
                        continue
                    if not is_recent(published, days=14):
                        report["discarded_old_date"] += 1
                        continue
                    title = vaga.get("title") or ""
                    url = vaga.get("url") or ""
                    cat = vaga.get("category") or ""
                    if not title or not url or url in seen_urls:
                        continue
                    if (cat in ("fora_escopo", "revisao_escopo", "outros", "") or
                        (cat == "designer" and not is_product_design_title(title)) or
                        is_vendas_vaga(vaga) or is_blacklisted(vaga)):
                        report["discarded_out_of_scope"] += 1
                        continue
                    seen_urls.add(url)
                    report["by_category"][cat] = report["by_category"].get(cat, 0) + 1
                    save_futures.append(sync_pool.submit(_persist_job, vaga))
        except FuturesTimeout:
            print("[RADAR] Tempo de coleta encerrado; preservando fontes gravadas")
        pending={f for f in scrape_futures if f not in completed}
        for future in pending:
            name=scrape_futures[future]
            report["sources"][name]["state"]="timeout"
            future.cancel()
        report["partial"]=bool(pending) or any(
            x.get("state") in ("error", "timeout") for x in report["sources"].values())
        for future in save_futures:
            try:
                if future.result():
                    report["synced_count"] += 1
                else:
                    # False tambem e falha: a versao antiga so contava excecoes.
                    report["persistence_errors"] += 1
            except Exception as e:
                report["persistence_errors"] += 1
                print(f"[RADAR] Persistência: {type(e).__name__}")
        if report["persistence_errors"]:
            report["partial"] = True
            print(f"[RADAR] {report['persistence_errors']} sincronizacoes nao confirmadas")
        # Zero vagas novas e uma situacao valida. Diferencie-a de falha de fonte.
        # Sem tentar gravar registros nao ha sincronizacao a confirmar.
        if save_futures and not report["synced_count"]:
            raise RuntimeError("Supabase não confirmou sincronização")
        report["candidates_with_valid_date"] = len(save_futures)
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
        print(f"[ERRO] {fn.__module__}: {type(e).__name__}")
        raise


if __name__ == "__main__":
    run()
