"""Plano único de buscas do Radar, distribuído entre fontes e famílias de cargos.

Cada execução consulta termos genéricos de todas as famílias e uma janela rotativa
da lista integral de títulos cadastrados. Não cria crons por categoria e não remove
títulos previamente solicitados. A classificação final continua feita em classify().
"""
from datetime import datetime, timezone
import os
import re
import unicodedata

DEFAULT_BATCH_SIZE = 5

FAMILIES = [
    ("crm", (r"\bcrm\b", r"relacionamento")),
    ("cxcs", (r"customer success", r"customer experience", r"\bcx\b", r"\bcs\b")),
    ("marketing", (r"marketing", r"martech")),
    ("salesforce", (r"salesforce", r"marketing cloud")),
    ("hubspot", (r"hubspot",)),
    ("growth", (r"growth", r"retention")),
    ("revops", (r"revops", r"revenue operations", r"sales ops")),
    ("data", (r"\bdados\b", r"\bdata\b", r"analytics")),
    ("ia", (r"inteligencia artificial", r"artificial intelligence", r"\bia\b", r"\bai\b")),
    ("product", (r"product design", r"\bux\b", r"\bui\b", r"designer")),
    ("product_owner", (r"product owner", r"product manager")),
    ("quality", (r"\bqa\b", r"quality assurance")),
    ("automation", (r"automacao", r"automation")),
    ("ecommerce", (r"e-commerce", r"ecommerce", r"marketplace")),
]

def _label(term):
    raw = term[0] if isinstance(term,(tuple,list)) else term
    chars = unicodedata.normalize('NFKD',str(raw or '').lower())
    chars = ''.join(c for c in chars if not unicodedata.combining(c))
    return re.sub(r"[_+\-]+"," ",chars)

def _balanced_terms(terms):
    """Intercala familias para nao gastar um ciclo inteiro em uma unica area."""
    groups = [[] for _ in FAMILIES]
    unmatched = []
    for term in dict.fromkeys(terms or ()):
        label = _label(term)
        family = next((i for i, (_, patterns) in enumerate(FAMILIES)
                       if any(re.search(pattern, label) for pattern in patterns)), None)
        (groups[family] if family is not None else unmatched).append(term)
    groups.append(unmatched)
    # Round-robin deterministico: todos os titulos permanecem na rotacao.
    result = []
    index = 0
    while any(index < len(group) for group in groups):
        for group in groups:
            if index < len(group):
                result.append(group[index])
        index += 1
    return result


def _claim_offset(source, total, limit):
    """Reserva atomica de um trecho do catalogo via Supabase.
    Sem credenciais (teste local), recai para rotacao diaria deterministica.
    """
    if total <= 0:
        return 0, False
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if url and key:
        try:
            import requests
            response = requests.post(
                url + "/rest/v1/rpc/claim_vagas_search_batch",
                headers={"apikey": key, "Authorization": "Bearer " + key,
                         "Content-Type": "application/json"},
                json={"p_source": source, "p_total": total, "p_batch": limit},
                timeout=6,
            )
            response.raise_for_status()
            rows = response.json()
            if isinstance(rows, list) and rows:
                return int(rows[0]["start_offset"]) % total, True
            raise ValueError("Reserva nao retornou cursor")
        except (ValueError, KeyError, TypeError, requests.RequestException) as exc:
            print("[RADAR] Cursor indisponivel (%s): %s" %
                  (source, type(exc).__name__))
    today = datetime.now(timezone.utc).date().toordinal()
    return (today * limit) % total, False


def select_search_batch(terms, source="", limit=None):
    """Um lote por fonte, com cobertura sem privilegio de CRM sobre outras familias.

    O cursor persiste entre invocacoes e percorre toda a lista sem saltar titulos.
    """
    ordered = _balanced_terms(terms)
    total = len(ordered)
    if not total:
        return [], {"offset": 0, "total": 0, "persisted": False}
    requested = int(limit or os.getenv("RADAR_QUERIES_PER_SOURCE", "20"))
    size = min(total, max(1, min(40, requested)))
    offset, persisted = _claim_offset(source, total, size)
    selected = [ordered[(offset + i) % total] for i in range(size)]
    return selected, {"offset": offset, "total": total,
                      "next_offset": (offset + size) % total,
                      "persisted": persisted}


def select_searches(terms, source="", limit=None, day_index=None):
    """Compatibilidade com testes e chamadas legadas."""
    ordered = _balanced_terms(terms)
    if not ordered:
        return []
    size = min(len(ordered), max(1, min(40, int(limit or DEFAULT_BATCH_SIZE))))
    ordinal = day_index if day_index is not None else datetime.now(timezone.utc).date().toordinal()
    start = (ordinal * size) % len(ordered)
    return [ordered[(start + i) % len(ordered)] for i in range(size)]
