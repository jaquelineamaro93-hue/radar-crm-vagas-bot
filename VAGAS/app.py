"""
Entrypoint WSGI para Vercel (Flask).
O cron do Vercel chama GET /api/scrape todo dia às 9h UTC.
"""
from flask import Flask, request, jsonify
import os

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"status": "online", "service": "Bot de Vagas CX/CS & Design"})


@app.route("/api/debug-raw", methods=["GET"])
def debug_raw():
    import requests as req
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
    urls = {
        "vagasremotas": "https://vagasremotas.net/category/oportunidades/",
        "indeed":       "https://br.indeed.com/jobs?q=designer+remoto&l=Remoto&fromage=30",
        "behance":      "https://www.behance.net/joblist?search=ux+designer&country=BR",
        "dribbble":     "https://dribbble.com/jobs?q=ux+designer&remote=true",
        "inhire":       "https://inhire.io/vagas?q=designer",
        "remotar":      "https://remotar.com.br/jobs?q=designer",
    }
    result = {}
    for name, url in urls.items():
        try:
            r = req.get(url, headers=headers, timeout=(5, 8), allow_redirects=True)
            html = r.text
            result[name] = {
                "status_code": r.status_code,
                "final_url": r.url,
                "html_len": len(html),
                "snippet": html[2000:3500].replace("\n", " ").strip(),
            }
        except Exception as e:
            result[name] = {"error": str(e)}
    return jsonify(result)


@app.route("/api/debug", methods=["GET"])
def debug():
    try:
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from scrapers import ALL_SCRAPERS

        report = {}

        def run_one(fn):
            name = fn.__module__.replace("scrapers.", "")
            t0 = time.time()
            try:
                vagas = fn()
                return name, {
                    "status": "ok", "count": len(vagas),
                    "elapsed_s": round(time.time() - t0, 2),
                    "sample": [
                        {"title": v.get("title"), "company": v.get("company"),
                         "published_at": v.get("published_at"), "url": v.get("url", "")[:80]}
                        for v in vagas[:3]
                    ],
                }
            except Exception as e:
                return name, {"status": "error", "error": str(e),
                               "elapsed_s": round(time.time() - t0, 2)}

        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(run_one, fn): fn for fn in ALL_SCRAPERS}
            try:
                for f in as_completed(futs, timeout=50):
                    name, result = f.result()
                    report[name] = result
            except Exception:
                pass

        total = sum(r.get("count", 0) for r in report.values())
        return jsonify({"total_vagas": total, "sources": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/scrape", methods=["GET"])
def scrape():
    cron_secret = os.environ.get("CRON_SECRET", "")
    auth = request.headers.get("Authorization", "")
    if cron_secret and auth != f"Bearer {cron_secret}":
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from main import run
        count = run()
        return jsonify({"status": "ok", "novas_vagas": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
