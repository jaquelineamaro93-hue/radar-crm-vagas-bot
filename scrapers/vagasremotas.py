"""
Scraper para vagasremotas.net — board WordPress de vagas remotas BR.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "VagasRemotas"
BASE_URL = "https://vagasremotas.net/category/oportunidades/"


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

    try:
        resp = session.get(BASE_URL, timeout=(5, 10))
        if resp.status_code != 200:
            print(f"[VagasRemotas] HTTP {resp.status_code}")
            return vagas

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("li.wp-block-post")

        for card in cards:
            title_el = card.select_one("h2.wp-block-post-title a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")

            time_el = card.select_one("div.wp-block-post-date time[datetime]")
            published_at = time_el.get("datetime") if time_el else None

            desc_el = card.select_one("p.wp-block-post-excerpt__excerpt")
            description = desc_el.get_text(strip=True) if desc_el else ""

            category = classify(title, description)
            if not category:
                continue

            vagas.append({
                "title": title,
                "company": "Não informado",
                "url": href,
                "location": "Remoto",
                "description": description,
                "source": SOURCE,
                "category": category,
                "published_at": published_at,
            })

    except Exception as e:
        print(f"[VagasRemotas] Erro: {e}")

    print(f"[VagasRemotas] {len(vagas)} vagas encontradas")
    return vagas
