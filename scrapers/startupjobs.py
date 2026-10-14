"""Vagas de startups com RSS público oficial e datas de publicação verificáveis.

O provedor disponibiliza feeds dos últimos 14 dias, sem chave de API.
Os títulos apontam para startup.jobs, com a fonte sempre atribuída.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .base import classify, is_recent

SOURCE = "Startup.jobs"
SEARCHES = [
    "https://startup.jobs/feeds/jobs",
    "https://startup.jobs/feeds/jobs?workplace=remote",
    "https://startup.jobs/feeds/jobs?role=marketing",
]
_HEADERS = {
    "User-Agent": "ConexaoCRMJobs/1.0 (public RSS; contact via conexaocrm.com)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
}
_ALLOWED_HOSTS = {"startup.jobs", "www.startup.jobs"}
_ATOM = "{http://www.w3.org/2005/Atom}"
_CONTENT = "{http://purl.org/rss/1.0/modules/content/}"


def _text(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _iso_date(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        date = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            date = parsedate_to_datetime(raw)
        except (ValueError, TypeError, IndexError):
            return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.isoformat()


def _safe_link(raw):
    url = (raw or "").strip()
    p = urlparse(url)
    return url if p.scheme == "https" and p.hostname in _ALLOWED_HOSTS else None


def _feed_entries(xml):
    root = ET.fromstring(xml)
    if root.tag.endswith("rss") or root.find("channel") is not None:
        for entry in root.findall(".//channel/item"):
            title = _text(entry, "title")
            url = _safe_link(_text(entry, "link"))
            published = _iso_date(_text(entry, "pubDate") or _text(entry, "published"))
            summary = _text(entry, _CONTENT + "encoded") or _text(entry, "description")
            yield title, url, published, summary
    else:
        for entry in root.findall(".//" + _ATOM + "entry"):
            title = _text(entry, _ATOM + "title")
            published = _iso_date(_text(entry, _ATOM + "published") or
                                  _text(entry, _ATOM + "updated"))
            url = next(
                (_safe_link(link.get("href")) for link in entry.findall(_ATOM + "link")
                 if link.get("rel", "alternate") == "alternate" and
                 _safe_link(link.get("href"))), None
            )
            summary = _text(entry, _ATOM + "summary") or _text(entry, _ATOM + "content")
            yield title, url, published, summary


def scrape(searches=None):
    vagas, seen = [], set()
    urls = list(searches if searches is not None else SEARCHES)
    http_ok, errors = 0, {}
    with requests.Session() as session:
        for feed_url in urls:
            if not _safe_link(feed_url):
                raise ValueError("RSS Startup.jobs fora do domínio autorizado")
            try:
                response = session.get(feed_url, headers=_HEADERS, timeout=(4, 10))
                if response.status_code != 200:
                    errors[response.status_code] = errors.get(response.status_code, 0) + 1
                    continue
                http_ok += 1
                for title, link, date, summary in _feed_entries(response.content):
                    if not title or not link or not date or link in seen:
                        continue
                    if not is_recent(date, 14):
                        continue
                    category = classify(title)
                    if not category:
                        continue
                    seen.add(link)
                    clean_summary = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)
                    vagas.append({
                        "title": title, "company": "Não informado",
                        "url": link, "location": "Não informado",
                        "description": clean_summary[:500],
                        "source": SOURCE, "category": category,
                        "published_at": date,
                    })
            except (requests.RequestException, ET.ParseError, ValueError) as exc:
                print(f"[Startup.jobs] Falha no RSS: {type(exc).__name__}")
                errors["parse_or_network"] = errors.get("parse_or_network", 0) + 1
    if urls and not http_ok:
        raise RuntimeError(f"Startup.jobs RSS indisponivel: {errors}")
    print(f"[Startup.jobs] {len(vagas)} vagas com data comprovada; RSS200={http_ok}")
    return vagas
