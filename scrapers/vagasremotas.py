"""Coleta publica de vagasremotas.com.br, com datas comprovadas."""
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .base import classify, extract_publication_date

SOURCE = "VagasRemotas.com.br"
BASE_URL = "https://vagasremotas.com.br"
SEARCHES = [
    BASE_URL + "/vagas-home-office-remoto/",
    BASE_URL + "/",
    BASE_URL + "/trabalho-home-office/vaga-nacional/",
]
_JOB_PATH = re.compile(r"^/vagas-home-office-remoto/[^/?#]+/?$")


def _list_links(html):
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select('a[href*="/vagas-home-office-remoto/"]'):
        url = urljoin(BASE_URL, link.get("href", ""))
        p = urlparse(url)
        if p.hostname in ("vagasremotas.com.br", "www.vagasremotas.com.br") and _JOB_PATH.match(p.path):
            yield url


def _published(soup):
    value = extract_publication_date(soup)
    if value:
        return value
    for name in ("article:published_time", "datePublished"):
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            try:
                dt = datetime.fromisoformat(tag["content"].replace("Z", "+00:00"))
                return dt.replace(tzinfo=timezone.utc).isoformat() if not dt.tzinfo else dt.isoformat()
            except (ValueError, TypeError):
                pass
    for node in soup.find_all(string=re.compile(r"(?:Data\s+Postada|Date\s+Posted)", re.I)):
        label = node.parent.get_text(" ", strip=True) if node.parent else str(node)
        m = re.search(
            r"(?:Data\s+Postada|Date\s+Posted)\s*:\s*(?:Posted\s*)?(\d+)\s*(horas?|hours?|dias?|days?|semanas?|weeks?|m[eê]s(?:es)?|months?)\s*(?:ago|atr[aá]s)?",
            label, re.I,
        )
        if m:
            count, unit = int(m.group(1)), m.group(2).casefold()
            days = count * (30 if "mes" in unit or "mês" in unit or "month" in unit else
                            7 if "sem" in unit or "week" in unit else 1)
            delta = timedelta(hours=count) if "hora" in unit or "hour" in unit else timedelta(days=days)
            return (datetime.now(timezone.utc) - delta).isoformat()
    return None


def _parse_job(html, url):
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    category = classify(title)
    published = _published(soup)
    if not title or not category or not published:
        return None
    company = next((node.get_text(" ", strip=True) for node in soup.select("h4, .company-name")
                    if 2 < len(node.get_text(" ", strip=True)) < 100), "Não informado")
    return {
        "title": title, "company": company, "url": url, "location": "Remoto",
        "description": (soup.find("main") or soup).get_text(" ", strip=True)[:500],
        "source": SOURCE, "category": category, "published_at": published,
    }


def scrape(searches=None):
    indices = list(searches if searches is not None else SEARCHES)
    jobs, seen, successful = [], set(), 0
    http_errors = {}
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ConexaoCRMJobs/1.0)", "Accept": "text/html,application/xhtml+xml", "Accept-Language": "pt-BR,pt;q=0.9"})
        for index in indices:
            if urlparse(index).hostname not in ("vagasremotas.com.br", "www.vagasremotas.com.br"):
                raise ValueError("Endereco fora do dominio")
            try:
                response = session.get(index, timeout=(4, 9))
                if response.status_code != 200:
                    http_errors[response.status_code] = http_errors.get(response.status_code, 0) + 1
                    continue
                successful += 1
                for url in _list_links(response.text):
                    if url in seen or len(seen) >= 12:
                        continue
                    seen.add(url)
                    detail = session.get(url, timeout=(3, 7))
                    if detail.status_code != 200:
                        continue
                    job = _parse_job(detail.text, url)
                    if job:
                        jobs.append(job)
            except requests.RequestException as exc:
                print(f"[VagasRemotas] Falha: {type(exc).__name__}")
    if indices and not successful:
        raise RuntimeError(f"VagasRemotas indices indisponiveis; HTTP={http_errors}")
    print(f"[VagasRemotas] {len(jobs)} vagas datadas em {len(seen)} detalhes")
    return jobs
