"""Coleta Gupy unificada para CRM, CX, CS, Marketing, IA, Dados, Product e demais famílias aprovadas.

A origem aceita diferentes modalidades; nunca restringir somente a remoto.
A função scrape(searches=...) é usada pelo orquestrador com plano equilibrado
e os termos completos continuam em SEARCHES para rotação entre execuções.
"""
import requests
from config import KEYWORDS, CXCS_SEARCH_TERMS
from .base import classify

SOURCE = "Gupy"
API_URL = "https://employability-portal.gupy.io/api/v1/jobs"
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

def scrape(searches=None) -> list[dict]:
    vagas=[]
    seen=set()
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
                    print(f"[Gupy] HTTP {resp.status_code} para {query!r}")
                    continue
                parsed=resp.json()
                jobs=parsed.get("data",[]) if isinstance(parsed,dict) else []
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
                    vagas.append({
                        "title":title,"company":job.get("careerPageName") or "Não informado",
                        "url":url,"location":location,
                        "description":str(job.get("description") or "")[:300],
                        "source":SOURCE,"category":category,
                        "published_at":job.get("publishedAt") or job.get("createdAt"),
                    })
            except (requests.RequestException, ValueError,TypeError) as error:
                print(f"[Gupy] Falha em {query!r}: {type(error).__name__}")
    print(f"[Gupy] {len(vagas)} vagas válidas em {len(planned)} consultas")
    return vagas
