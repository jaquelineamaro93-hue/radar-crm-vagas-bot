"""
Scraper para LinkedIn Jobs (busca pública, sem login).
"""
import time
import requests
from .base import classify, relative_to_iso

SOURCE = "LinkedIn"

# (keyword, location, f_WT, f_TPR)
# f_WT: "1"=presencial, "2"=remoto
# f_TPR: r2592000=30d, r5184000=60d
SEARCHES = [
    # DADOS — 60 dias, populate inicial
    ("analista de dados", "Brazil", "2", "r5184000"),
    ("data analyst", "Brazil", "2", "r5184000"),
    ("cientista de dados", "Brazil", "2", "r5184000"),
    ("data scientist", "Brazil", "2", "r5184000"),
    ("engenheiro de dados", "Brazil", "2", "r5184000"),
    ("data engineer", "Brazil", "2", "r5184000"),
    ("analytics engineer", "Brazil", "2", "r5184000"),
    ("machine learning engineer", "Brazil", "2", "r5184000"),
    ("business intelligence", "Brazil", "2", "r5184000"),
    # PO / PM — 60 dias, populate inicial
    ("product owner", "Brazil", "2", "r5184000"),
    ("product manager", "Brazil", "2", "r5184000"),
    ("gerente de produto", "Brazil", "2", "r5184000"),
    ("head de produto", "Brazil", "2", "r5184000"),
    ("product lead remoto", "Brazil", "2", "r5184000"),
    # QA — 60 dias, populate inicial
    ("analista de qualidade remoto", "Brazil", "2", "r5184000"),
    ("quality analyst", "Brazil", "2", "r5184000"),
    ("qa engineer", "Brazil", "2", "r5184000"),
    ("analista de testes remoto", "Brazil", "2", "r5184000"),
    ("quality assurance remoto", "Brazil", "2", "r5184000"),
    ("sdet", "Brazil", "2", "r5184000"),
    # CRM PRIMEIRO — 60 dias, prioridade máxima para populate inicial
    ("analista crm", "Brazil", "2", "r5184000"),
    ("analista de crm", "Brazil", "2", "r5184000"),
    ("crm specialist", "Brazil", "2", "r5184000"),
    ("salesforce administrator", "Brazil", "2", "r5184000"),
    ("salesforce analyst", "Brazil", "2", "r5184000"),
    ("salesforce developer", "Brazil", "2", "r5184000"),
    ("crm manager", "Brazil", "2", "r5184000"),
    # Designer (remoto)
    ("designer remoto", "Brazil", "2", "r2592000"),
    ("customer success remoto", "Brazil", "2", "r2592000"),
    ("customer experience remoto", "Brazil", "2", "r2592000"),
    ("UX UI product designer", "Brazil", "2", "r2592000"),
    # Dev (remoto)
    ("desenvolvedor remoto", "Brazil", "2", "r2592000"),
    ("programador remoto", "Brazil", "2", "r2592000"),
    ("developer remote", "Brazil", "2", "r2592000"),
    ("frontend developer remoto", "Brazil", "2", "r2592000"),
    ("backend developer remoto", "Brazil", "2", "r2592000"),
    ("fullstack developer remoto", "Brazil", "2", "r2592000"),
    ("software engineer remoto", "Brazil", "2", "r2592000"),
    # Tech Lead / Gestão de Tecnologia (remoto)
    ("tech lead remoto", "Brazil", "2", "r2592000"),
    ("engineering manager", "Brazil", "2", "r2592000"),
    ("gerente de engenharia", "Brazil", "2", "r2592000"),
    ("gerente de tecnologia", "Brazil", "2", "r2592000"),
    ("head of engineering", "Brazil", "2", "r2592000"),
    ("CTO remoto", "Brazil", "2", "r2592000"),
    # Ed. Física — remoto
    ("professor educação física remoto", "Brazil", "2", "r2592000"),
    ("personal trainer remoto", "Brazil", "2", "r2592000"),
    ("preparador físico remoto", "Brazil", "2", "r2592000"),
    # Ed. Física — presencial em São Paulo
    ("professor educação física", "São Paulo, Brazil", "1", "r2592000"),
    ("personal trainer", "São Paulo, Brazil", "1", "r2592000"),
    ("preparador físico", "São Paulo, Brazil", "1", "r2592000"),
    ("instrutor academia", "São Paulo, Brazil", "1", "r2592000"),
    ("professor musculação", "São Paulo, Brazil", "1", "r2592000"),
]

BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def scrape() -> list[dict]:
    vagas = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for keyword, location, f_wt, f_tpr in SEARCHES:
        params = {
            "keywords": keyword,
            "location": location,
            "f_WT": f_wt,
            "f_TPR": f_tpr,
            "start": 0,
        }
        try:
            resp = session.get(BASE_URL, params=params, timeout=(5, 8))
            if resp.status_code != 200:
                continue
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.select("li"):
                title_el = card.select_one(".base-search-card__title, h3")
                company_el = card.select_one(".base-search-card__subtitle, h4")
                location_el = card.select_one(".job-search-card__location")
                time_el = card.select_one("time[datetime]")
                link_el = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Não informado"
                loc = location_el.get_text(strip=True) if location_el else "Remoto"
                url = link_el.get("href", "").split("?")[0]

                # Data de publicação
                published_at = None
                if time_el:
                    published_at = time_el.get("datetime")  # formato: "2024-01-15"
                    if published_at and len(published_at) == 10:
                        published_at = published_at + "T00:00:00+00:00"

                category = classify(title)
                if not category:
                    continue

                vagas.append({
                    "title": title, "company": company,
                    "url": url, "location": loc,
                    "description": "", "source": SOURCE,
                    "category": category, "published_at": published_at,
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"[LinkedIn] {keyword}: {e}")

    print(f"[LinkedIn] {len(vagas)} vagas encontradas")
    return vagas
