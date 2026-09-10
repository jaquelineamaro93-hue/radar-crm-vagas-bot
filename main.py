"""
Orquestrador principal.
Roda os scrapers em paralelo para caber no timeout de 60s do Vercel.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from database import init_db, is_duplicate, save_vaga, upload_to_supabase, is_vendas_vaga, is_blacklisted
# Notifier removido
from supabase_sync import sync_vaga_crm
from scrapers import ALL_SCRAPERS
from scrapers.base import is_recent

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
    # Ed. Física: aceita remoto OU presencial em São Paulo
    if cat == "edfis":
        return _is_remote(vaga) or _is_sao_paulo(vaga)
    return _is_remote(vaga)


def run() -> int:
    print("=" * 50)
    print("Iniciando coleta de vagas...")

    init_db()

    all_vagas: list[dict] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_safe_scrape, fn): fn.__module__ for fn in ALL_SCRAPERS}
        try:
            for future in as_completed(futures, timeout=120):
                all_vagas.extend(future.result())
        except Exception as e:
            print(f"[WARN] Timeout global — {e}")

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

    total_novas = 0
    erros = 0
    for vaga in filtradas:
        if not vaga.get("title") or not vaga.get("url"):
            continue
        if is_duplicate(vaga["title"], vaga.get("company", ""), vaga["url"]):
            continue
        if is_vendas_vaga(vaga):
            continue
        if is_blacklisted(vaga):
            continue

        try:
            save_vaga(vaga)
            upload_to_supabase(vaga)
            sync_vaga_crm(vaga)
            total_novas += 1
        except Exception as e:
            print(f"[ERRO] Falha ao inserir vaga '{vaga.get('title', '?')[:50]}': {e}")
            erros += 1
        time.sleep(0.15)

    print(f"Novas vagas: {total_novas} | Erros: {erros}")
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
