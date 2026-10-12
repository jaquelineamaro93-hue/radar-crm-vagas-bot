"""Non-destructive job availability checks.

Never DELETE listings: saved-job relations and the original catalog remain intact.
403/429/400 are NOT evidence that a vacancy is closed.
Only repeated 404/410 on approved job hosts (with a >=24h gap) is a closure signal.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import os
import requests

_ALLOWED = ("gupy.io", "vagas.com.br", "catho.com.br", "infojobs.com.br",
            "linkedin.com", "99jobs.com", "solides.jobs")
_LIMIT = 16


def _hostname(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not any(host == d or host.endswith("." + d) for d in _ALLOWED):
            return None
        return host
    except (ValueError, TypeError):
        return None


def _closure_signal(code, host):
    if code == 410:
        return True
    return code == 404 and not (host == "linkedin.com" or host.endswith(".linkedin.com"))


def next_status(code, host, old_status="unverified", failures=0, previous_check=None, now=None):
    """Calculate availability without treating bot-blocking responses as closures."""
    now = now or datetime.now(timezone.utc)
    failures = max(0, int(failures or 0))
    if _closure_signal(code, host):
        previous = None
        if previous_check:
            try:
                previous = datetime.fromisoformat(previous_check.replace("Z", "+00:00"))
                if previous.tzinfo is None:
                    previous = previous.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        if not previous or now - previous >= timedelta(hours=24):
            failures += 1
        return ("closed" if failures >= 2 else "suspected_closed"), failures
    if code == 200:
        # HTTP 200 alone does not prove an employer still accepts applications.
        return ("closed" if old_status == "closed" else "unverified"), 0
    return old_status, failures


def _probe(item):
    url = item.get("url") or ""
    host = _hostname(url)
    if not host:
        return item, None, None
    try:
        with requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ConexaoCRMJobVerifier/1.0)"},
                          allow_redirects=False, stream=True, timeout=(2.5, 4)) as response:
            return item, response.status_code, host
    except requests.RequestException:
        return item, None, host


def check_closed_jobs(limit=_LIMIT):
    """Check a small, rotating batch of old vacancies, only PATCH metadata."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return {"checked": 0, "suspected": 0, "closed": 0, "skipped": True}
    headers = {"apikey": key, "Authorization": f"Bearer {key}",
               "Content-Type": "application/json", "Prefer": "return=minimal"}
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=7)).isoformat()
    response = requests.get(
        f"{url}/rest/v1/vagas_crm", headers=headers,
        params={"select": "id,url,source,availability_status,closure_failures,availability_checked_at",
                "availability_status": "neq.closed",
                "found_at": "lt." + cutoff,
                "or": "(last_seen_at.is.null,last_seen_at.lt." + cutoff + ")",
                "order": "availability_checked_at.asc.nullsfirst",
                "limit": str(min(max(int(limit), 1), 25))},
        timeout=(3, 7))
    response.raise_for_status()
    jobs = response.json()
    report = {"checked": 0, "suspected": 0, "closed": 0, "skipped": False}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed([pool.submit(_probe, item) for item in jobs]):
            item, status_code, host = future.result()
            if not host or status_code is None:
                # Rotate unverifiable URLs without declaring them closed.
                status, failures = (item.get("availability_status") or "unverified",
                                    item.get("closure_failures") or 0)
            else:
                status, failures = next_status(
                    status_code, host,
                    item.get("availability_status") or "unverified",
                    item.get("closure_failures") or 0,
                    item.get("availability_checked_at"), now)
            payload = {"availability_checked_at": now.isoformat(),
                       "availability_status": status,
                       "closure_failures": failures}
            try:
                patch = requests.patch(
                    f"{url}/rest/v1/vagas_crm", headers=headers,
                    params={"id": "eq." + str(int(item["id"]))},
                    json=payload, timeout=(3, 5))
                if not patch.ok:
                    continue
                report["checked"] += 1
                if status == "suspected_closed":
                    report["suspected"] += 1
                elif status == "closed":
                    report["closed"] += 1
            except (requests.RequestException, ValueError, KeyError):
                continue
    return report
