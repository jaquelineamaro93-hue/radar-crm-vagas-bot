"""
Scraper para Gupy — maior ATS/job board do Brasil.
Usa a API pública de busca de vagas.
"""
import requests
from .base import classify

SOURCE = "Gupy"
API_URL = "https://portal.api.gupy.io/api/v1/jobs"


def scrape() -> list[dict]:
    vagas = []
    seen_urls: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Origin": "https://portal.gupy.io",
        "Referer": "https://portal.gupy.io/",
    })

    # (query, extra_params)
    searches = [
        # ── Designer (remoto) ─────────────────────────────────────────────────
        ("designer",                  {"isRemoteWork": "true"}),
        ("ux designer",               {"isRemoteWork": "true"}),
        ("product designer",          {"isRemoteWork": "true"}),
        ("ui designer",               {"isRemoteWork": "true"}),
        ("web designer",              {"isRemoteWork": "true"}),
        ("motion designer",           {"isRemoteWork": "true"}),
        ("designer gráfico",          {"isRemoteWork": "true"}),
        # ── CX / CS (remoto) ─────────────────────────────────────────────────
        ("customer success",          {"isRemoteWork": "true"}),
        ("customer experience",       {"isRemoteWork": "true"}),
        ("analista atendimento",      {"isRemoteWork": "true"}),
        ("suporte ao cliente",        {"isRemoteWork": "true"}),
        ("analista de suporte",       {"isRemoteWork": "true"}),
        ("account manager",           {"isRemoteWork": "true"}),
        # ── Dev (remoto) ─────────────────────────────────────────────────────
        ("desenvolvedor",             {"isRemoteWork": "true"}),
        ("programador",               {"isRemoteWork": "true"}),
        ("developer",                 {"isRemoteWork": "true"}),
        ("frontend",                  {"isRemoteWork": "true"}),
        ("backend",                   {"isRemoteWork": "true"}),
        ("fullstack",                 {"isRemoteWork": "true"}),
        ("software engineer",         {"isRemoteWork": "true"}),
        ("devops",                    {"isRemoteWork": "true"}),
        ("tech lead",                 {"isRemoteWork": "true"}),
        ("engineering manager",       {"isRemoteWork": "true"}),
        ("gerente de tecnologia",     {"isRemoteWork": "true"}),
        ("gerente de engenharia",     {"isRemoteWork": "true"}),
        ("head de tecnologia",        {"isRemoteWork": "true"}),
        ("cto",                       {"isRemoteWork": "true"}),
        # ── Dados (remoto) ───────────────────────────────────────────────────
        ("analista de dados",         {"isRemoteWork": "true"}),
        ("data analyst",              {"isRemoteWork": "true"}),
        ("cientista de dados",        {"isRemoteWork": "true"}),
        ("data scientist",            {"isRemoteWork": "true"}),
        ("engenheiro de dados",       {"isRemoteWork": "true"}),
        ("data engineer",             {"isRemoteWork": "true"}),
        ("machine learning",          {"isRemoteWork": "true"}),
        ("business intelligence",     {"isRemoteWork": "true"}),
        ("analytics engineer",        {"isRemoteWork": "true"}),
        ("power bi",                  {"isRemoteWork": "true"}),
        # ── PO / PM (remoto) ─────────────────────────────────────────────────
        ("product owner",             {"isRemoteWork": "true"}),
        ("product manager",           {"isRemoteWork": "true"}),
        ("gerente de produto",        {"isRemoteWork": "true"}),
        ("head de produto",           {"isRemoteWork": "true"}),
        # ── QA (remoto) ───────────────────────────────────────────────────────
        ("analista de qualidade",     {"isRemoteWork": "true"}),
        ("analista de testes",        {"isRemoteWork": "true"}),
        ("quality analyst",           {"isRemoteWork": "true"}),
        ("qa engineer",               {"isRemoteWork": "true"}),
        ("quality assurance",         {"isRemoteWork": "true"}),
        ("tester",                    {"isRemoteWork": "true"}),
        # ── CRM (remoto) ─────────────────────────────────────────────────────
        ("analista de crm",           {"isRemoteWork": "true"}),
        ("analista salesforce",       {"isRemoteWork": "true"}),
        ("crm specialist",            {"isRemoteWork": "true"}),
        ("salesforce administrator",  {"isRemoteWork": "true"}),
        ("salesforce developer",      {"isRemoteWork": "true"}),
        ("hubspot",                   {"isRemoteWork": "true"}),
        # ── Ed. Física — remoto ───────────────────────────────────────────────
        ("professor educação física", {"isRemoteWork": "true"}),
        ("personal trainer",          {"isRemoteWork": "true"}),
        ("preparador físico",         {"isRemoteWork": "true"}),
        # ── Ed. Física — presencial SP ────────────────────────────────────────
        ("professor educação física", {"state": "SP"}),
        ("personal trainer",          {"state": "SP"}),
        ("preparador físico",         {"state": "SP"}),
        ("instrutor musculação",      {"state": "SP"}),
        ("instrutor de academia",     {"state": "SP"}),
    ]

    for query, extra in searches:
        try:
            params = {
                "jobName": query,
                "limit": 20,
                "offset": 0,
                **extra,
            }
            resp = session.get(API_URL, params=params, timeout=(5, 8))
            if resp.status_code != 200:
                continue

            data = resp.json()
            jobs = data.get("data", [])

            for job in jobs:
                url = job.get("jobUrl", "") or f"https://portal.gupy.io/job/{job.get('id', '')}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = job.get("name", "")
                company = job.get("careerPageName", "Não informado")
                city = job.get("city", "")
                state = job.get("state", "")
                loc = f"{city}, {state}".strip(", ") if (city or state) else "Remoto"

                category = classify(title)
                if not category:
                    continue

                vagas.append({
                    "title": title,
                    "company": company,
                    "url": url,
                    "location": loc,
                    "description": job.get("description", "")[:300],
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,  # API pública não retorna data
                })

        except Exception as e:
            print(f"[Gupy] Erro em '{query}': {e}")

    print(f"[Gupy] {len(vagas)} vagas encontradas")
    return vagas
