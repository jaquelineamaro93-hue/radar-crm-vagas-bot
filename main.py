"""
Orquestrador principal.
Roda os scrapers em paralelo para caber no timeout de 60s do Vercel.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from database import init_db, is_duplicate, save_vaga, upload_to_supabase, is_blacklisted
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
            for future in as_completed(futures, timeout=50):
                all_vagas.extend(future.result())
        except Exception:
            print("[WARN] Timeout global — usando vagas coletadas até agora")

    # Filtra: localização válida por categoria + publicadas no período por categoria
    # CRM: 60 dias (populate inicial); demais: 30 dias
    def _days_for(vaga: dict) -> int:
        return 60 if vaga.get("category") in ("crm", "data", "po_pm", "qa") else 30

    filtradas = [
        v for v in all_vagas
        if _passes_location_filter(v) and is_recent(v.get("published_at"), days=_days_for(v))
    ]
    print(f"Total coletado: {len(all_vagas)} | Após filtros (remoto + 30 dias): {len(filtradas)}")

    total_novas = 0
    for vaga in filtradas:
        if not vaga.get("title") or not vaga.get("url"):
            continue
        if is_duplicate(vaga["title"], vaga.get("company", ""), vaga["url"]):
            continue

        save_vaga(vaga)
        upload_to_supabase(vaga)


        upload_to_supabase(vaga)
        upload_to_supabase(vaga)
            # send_vaga removido
        sync_vaga_crm(vaga)
        total_novas += 1
        time.sleep(0.15)  # rate limit Discord (~6 msg/s, abaixo do limite de 5/2s por webhook)

    print(f"Novas vagas enviadas ao Discord: {total_novas}")
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
