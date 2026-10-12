"""Persistent run history in Supabase. Failures never block the job."""
import os
import uuid
import requests
from datetime import datetime, timezone

def _settings():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None, None
    return url + "/rest/v1/vagas_cron_run_history", {
        "apikey": key, "Authorization": "Bearer " + key,
        "Content-Type": "application/json", "Prefer": "return=minimal"
    }

def begin(job_name):
    run_id = str(uuid.uuid4())
    url, headers = _settings()
    if url:
        try:
            r = requests.post(url, headers=headers, timeout=4, json={
                "id": run_id, "job_name": job_name, "status": "running",
                "source": "vercel_cron"
            })
            if not r.ok:
                print(f"[CRON_HISTORY] begin HTTP {r.status_code}")
        except requests.RequestException as exc:
            print(f"[CRON_HISTORY] begin unavailable: {type(exc).__name__}")
    return run_id

def finish(run_id, success, count=0, error=None, details=None):
    url, headers = _settings()
    if not url:
        return
    payload = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "status": "success" if success else "error",
        "synced_count": max(0, int(count or 0)),
        "error_summary": str(error)[:400] if error else None,
        "details": details or {}
    }
    try:
        r = requests.patch(url, headers=headers, params={"id": "eq." + run_id},
                           json=payload, timeout=4)
        if not r.ok:
            print(f"[CRON_HISTORY] finish HTTP {r.status_code}")
    except requests.RequestException as exc:
        print(f"[CRON_HISTORY] finish unavailable: {type(exc).__name__}")
