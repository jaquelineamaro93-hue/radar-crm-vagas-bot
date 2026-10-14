"""Coleta Gupy unificada para CRM, CX, CS, Marketing, IA, Dados, Product e demais famílias aprovadas.

A origem aceita diferentes modalidades; nunca restringir somente a remoto.
A função scrape(searches=...) é usada pelo orquestrador com plano equilibrado
e os termos completos continuam em SEARCHES para rotação entre execuções.
"""
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse
from config import KEYWORDS, CXCS_SEARCH_TERMS
from .base import classify

SOURCE = "Gupy"
API_URL = "https://portal.gupy.io/api/job-search/jobs"
APPROVED_FAMILIES = (
    "crm", "cxcs", "marketing", "designer", "revops", "salesops",
    "ia", "data", "po_pm", "qa", "tech", "automacao",
    "automacao_presencial", "automacao_remote"
)
BASE_SEARCHES = [
    "crm", "analista de crm", "customer success", "customer experience",
    "marketing", "salesforce", "hubspot", "growth", "revops", "e-commerce",
    "product designer", "designer de produto", "analista de dados",
    "inteligencia artificial", "quality assurance", "automacao",
]
SEARCHES = list(dict.fromkeys(
    BASE_SEARCHES + list(CXCS_SEARCH_TERMS) +
    [term for category in APPROVED_FAMILIES for term in KEYWORDS.get(category,[])]
))

def _verified_open(job, now=None):
    """Somente anuncio publicado com prazo de candidatura futuro, na busca viva.

    Sem prazo comprovado, o anuncio fica sem selo de aberta e nao entra
    na listagem de vagas abertas. HTTP 200 sozinho nao prova isso.
    """
    if not isinstance(job, dict):
        return False
    if job.get("isOpen") is False or job.get("isActive") is False:
        return False
    status = str(job.get("status") or job.get("jobStatus") or "").casefold()
    if status in {"closed", "expired", "inactive", "cancelled", "encerrada", "encerrado"}:
        return False
    link = job.get("jobUrl") or ""
    parsed = urlparse(link)
    if parsed.scheme != "https" or not (
        parsed.hostname == "gupy.io" or (parsed.hostname or "").endswith(".gupy.io")
    ):
        return False
    raw = job.get("applicationDeadline")
    if not raw:
        return False
    try:
        deadline = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return False
    return deadline >= (now or datetime.now(timezone.utc))


def scrape(searches=None) -> list[dict]:
    vagas=[]
    seen=set()
    http_ok = 0
    http_errors = {}
    planned = list(searches) if searches is not None else SEARCHES
    with requests.Session() as session:
        session.headers.update({
            "User-Agent":"Mozilla/5.0 (compatible; ConexaoCRMJobs/1.0)",
            "Accept":"application/json",
        })
        for query in planned:
            try:
                # Não limitar a remoto: o portal também precisa de vagas híbridas/presenciais.
                resp=session.get(API_URL,params={"jobName":query,"limit":20,"offset":0},timeout=(3,8))
                if resp.status_code != 200:
                    http_errors[resp.status_code] = http_errors.get(resp.status_code, 0) + 1
                    print(f"[Gupy] HTTP {resp.status_code} para {query!r}")
                    continue
                http_ok += 1
                parsed=resp.json()
                jobs=parsed.get("data",[]) if isinstance(parsed,dict) else (parsed if isinstance(parsed,list) else [])
                for job in jobs:
                    if not isinstance(job,dict):continue
                    title=job.get("name") or job.get("title") or ""
                    url=job.get("jobUrl") or f"https://portal.gupy.io/job/{job.get('id','')}"
                    if not title or not url or url in seen:continue
                    category=classify(title)
                    if not category:continue
                    seen.add(url)
                    city=job.get("city") or ""
                    state=job.get("state") or ""
                    location=", ".join(str(x) for x in (city,state) if x) or "Brasil"
                    # Sem prova de prazo aberto nao anunciar como ativa.
                    if not _verified_open(job):
                        continue
                    vagas.append({
                        "title":title,"company":job.get("careerPageName") or "Não informado",
                        "url":url,"location":location,
                        "description":str(job.get("description") or "")[:300],
                        "source":SOURCE,"category":category,
                        "published_at":job.get("publishedDate") or job.get("publishedAt") or job.get("createdAt"),
                        "availability_evidence":"gupy_open_deadline",
                        "availability_checked_at":datetime.now(timezone.utc).isoformat(),
                    })
            except (requests.RequestException, ValueError,TypeError) as error:
                print(f"[Gupy] Falha em {query!r}: {type(error).__name__}")
    if planned and http_ok == 0 and http_errors:
        raise RuntimeError(f"Gupy indisponivel: HTTP {http_errors}")
    print(f"[Gupy] {len(vagas)} vagas válidas em {len(planned)} consultas; HTTP200={http_ok}; erros={http_errors}")
    return vagas
