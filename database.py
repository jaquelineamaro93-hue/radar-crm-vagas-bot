"""
Deduplicação de vagas — dois níveis de hash:

  vaga:{url_hash}  → SHA-256(title|company|url)
                     Detecta a mesma URL postada de novo.

  sem:{sem_hash}   → SHA-256(normalize(company)|normalize(title))
                     Detecta a mesma vaga em fontes diferentes
                     (LinkedIn + Gupy, InfoJobs + Vagas.com, etc.).
                     Só ativo quando a empresa é conhecida.

Usa Upstash Redis quando configurado; cai para SQLite em modo local.
"""
import hashlib
import re
import unicodedata
import os
from config import UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, DB_PATH

# TTL dos hashes no Redis: 90 dias
HASH_TTL = 60 * 60 * 24 * 90

_redis = None


def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
        from upstash_redis import Redis
        _redis = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)
    return _redis


def _use_redis() -> bool:
    return bool(UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)


# ── Normalização para hash semântico ─────────────────────────────────────────

_SENIORITY_NOISE = re.compile(
    r"\b(jr|junior|pl|pleno|sr|sênior|senior|snr|mid|i|ii|iii|"
    r"trainee|estagio|estágio|intern|associate|assistente|assistant|"
    r"level|nivel|nível|especialista)\b"
)
# Empresas que não identificam a vaga de forma única
_UNKNOWN_COMPANIES = {
    "", "nao informado", "nao informada", "não informado", "não informada",
    "not provided", "empresa nao informada", "empresa não informada",
    "confidencial", "unknown", "a confirmar",
}


def _normalize(text: str) -> str:
    """Remove acentos, pontuação, palavras de nível e colapsa espaços."""
    # Desacentua
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)           # remove pontuação
    text = _SENIORITY_NOISE.sub("", text)           # remove seniority
    return re.sub(r"\s+", " ", text).strip()


def make_hash(title: str, company: str, url: str) -> str:
    """Hash exato baseado em URL — evita reenvio da mesma postagem."""
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def make_semantic_hash(title: str, company: str) -> str:
    """
    Hash semântico empresa+título normalizado.
    Detecta a mesma vaga publicada em fontes diferentes.
    Retorna '' quando a empresa é desconhecida (hash inútil nesse caso).
    """
    norm_co = _normalize(company)
    if norm_co in _UNKNOWN_COMPANIES:
        return ""
    norm_title = _normalize(title)
    return hashlib.sha256(f"{norm_co}|{norm_title}".encode()).hexdigest()


# ── SQLite fallback ──────────────────────────────────────────────────────────

def _init_sqlite():
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vagas (
                hash      TEXT PRIMARY KEY,
                title     TEXT,
                company   TEXT,
                url       TEXT,
                source    TEXT,
                category  TEXT,
                found_at  TEXT
            )
        """)
        # Tabela de hashes semânticos (company+title)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sem_hashes (
                hash     TEXT PRIMARY KEY,
                found_at TEXT
            )
        """)
        conn.commit()


def _sqlite_is_dup(h: str) -> bool:
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT 1 FROM vagas WHERE hash=?", (h,)
        ).fetchone() is not None


def _sqlite_sem_is_dup(h: str) -> bool:
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT 1 FROM sem_hashes WHERE hash=?", (h,)
        ).fetchone() is not None


def _sqlite_save(h: str, vaga: dict):
    import sqlite3
    from datetime import datetime
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO vagas "
            "(hash,title,company,url,source,category,found_at) VALUES(?,?,?,?,?,?,?)",
            (h, vaga["title"], vaga.get("company", ""), vaga["url"],
             vaga.get("source", ""), vaga.get("category", ""),
             datetime.utcnow().isoformat()),
        )
        conn.commit()


def _sqlite_sem_save(h: str):
    import sqlite3
    from datetime import datetime
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sem_hashes (hash, found_at) VALUES(?, ?)",
            (h, datetime.utcnow().isoformat()),
        )
        conn.commit()


# ── Public API ───────────────────────────────────────────────────────────────

def init_db():
    if not _use_redis():
        _init_sqlite()


def is_duplicate(title: str, company: str, url: str) -> bool:
    url_h = make_hash(title, company, url)
    sem_h = make_semantic_hash(title, company)

    if _use_redis():
        r = _get_redis()
        # Checa hash exato (URL)
        if r.exists(f"vaga:{url_h}"):
            return True
        # Checa hash semântico (empresa+título normalizado)
        if sem_h and r.exists(f"sem:{sem_h}"):
            return True
        return False

    # SQLite
    if _sqlite_is_dup(url_h):
        return True
    if sem_h and _sqlite_sem_is_dup(sem_h):
        return True
    return False


def save_vaga(vaga: dict):
    url_h = make_hash(vaga["title"], vaga.get("company", ""), vaga["url"])
    sem_h = make_semantic_hash(vaga["title"], vaga.get("company", ""))

    if _use_redis():
        r = _get_redis()
        r.set(f"vaga:{url_h}", "1", ex=HASH_TTL)
        if sem_h:
            r.set(f"sem:{sem_h}", "1", ex=HASH_TTL)
    else:
        _sqlite_save(url_h, vaga)
        if sem_h:
            _sqlite_sem_save(sem_h)



def upload_to_supabase(vaga: dict):
    """Salva vaga no Supabase vagas_scraper"""
    import requests
    import os
    
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    
    if not url or not key:
        return False
    
    try:
        resp = requests.post(
            f"{url}/rest/v1/vagas_scraper",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json=vaga,
            timeout=10
        )
        return resp.status_code in (201, 204)
    except Exception as e:
        print(f"[WARN] Erro ao salvar no Supabase: {e}")
        return False
