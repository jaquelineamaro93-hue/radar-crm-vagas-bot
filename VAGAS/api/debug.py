"""
Endpoint de diagnóstico — testa cada scraper e retorna um relatório.
Não salva no Redis nem envia ao Discord.
Acesse: GET /api/debug
"""
from flask import Flask, jsonify
import os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)


@app.route("/api/debug", methods=["GET"])
def debug():
    from scrapers import ALL_SCRAPERS

    report = {}

    def run_one(fn):
        name = fn.__module__.replace("scrapers.", "")
        start = time.time()
        try:
            vagas = fn()
            elapsed = round(time.time() - start, 2)
            return name, {
                "status": "ok",
                "count": len(vagas),
                "elapsed_s": elapsed,
                "sample": [
                    {"title": v.get("title"), "company": v.get("company"),
                     "published_at": v.get("published_at"), "url": v.get("url", "")[:80]}
                    for v in vagas[:3]
                ],
            }
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            return name, {"status": "error", "error": str(e), "elapsed_s": elapsed}

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(run_one, fn): fn for fn in ALL_SCRAPERS}
        try:
            for future in as_completed(futures, timeout=50):
                name, result = future.result()
                report[name] = result
        except Exception:
            pass

    total = sum(r.get("count", 0) for r in report.values())
    return jsonify({"total_vagas": total, "sources": report})
