"""
Scraper para Behance Jobs (seção de empregos de design).
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Behance"

SEARCHES = [
    "ux designer", "ui designer", "product designer",
    "graphic designer", "web designer", "motion designer", "branding designer",
]
BASE_URL = "https://www.behance.net/joblist"


def scrape() -> list[dict]:
    vagas = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "x-requested-with": "XMLHttpRequest",
        "Referer": "https://www.behance.net/joblist",
    })

    for query in SEARCHES:
        try:
            params = {"search": query, "country": "BR", "sort": "featured"}
            resp = session.get(BASE_URL, params=params, timeout=(5, 10))
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Behance usa SSR — tenta pegar cards de vaga
            cards = soup.select("div.JobCard-jobCard-*, li[class*='JobCard']")

            for card in cards:
                title_el = card.select_one("h2, [class*='jobTitle'], [class*='title']")
                company_el = card.select_one("[class*='company'], [class*='Company']")
                link_el = card.select_one("a[href*='/joblist/']")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Não informado"
                url = link_el.get("href", "") if link_el else ""
                if url and not url.startswith("http"):
                    url = f"https://www.behance.net{url}"

                category = classify(title)
                if not category:
                    continue

                time_el = card.select_one("time[datetime], [class*='date']")
                published_at = time_el.get("datetime") if time_el else None
                vagas.append({
                    "title": title, "company": company,
                    "url": url, "location": "Remoto",
                    "description": "", "source": SOURCE,
                    "category": category, "published_at": published_at,
                })

        except Exception as e:
            print(f"[Behance] Erro: {e}")

    print(f"[Behance] {len(vagas)} vagas encontradas")
    return vagas
