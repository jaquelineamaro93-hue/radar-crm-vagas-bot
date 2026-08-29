MATCH_ROUTES_CODE = '''

# ============ MATCH POR IA (candidates / freelancers / platforms) ============
import csv as _csv
import io as _io
import re as _re
from urllib.request import Request as _Request, urlopen as _urlopen

_SUPABASE_URL_MATCH = "https://rwkbpafpniwzvlkfngag.supabase.co"
_SUPABASE_ANON_KEY_MATCH = "sb_publishable_41a2jzlzwZgFrdMJ6UpDXQ_jysf69_C"

_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtuTLaOZzk-uRDdRchwdNmypGJ8eO2K7qdckkL7Sh0VohIa8OHWMDbKuDDHQMsoLYOhMfIMlplKoop/pub"
    "?gid=692217056&single=true&output=csv"
)

_MAX_CANDIDATES_TO_SEND = 200
_MAX_RESULTS = 8


@app.after_request
def _add_cors_headers_match(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/match-candidates", methods=["POST", "OPTIONS"])
def match_candidates():
    if request.method == "OPTIONS":
        return "", 204
    try:
        body = request.get_json(force=True, silent=True) or {}
        job_description = (body.get("jobDescription") or "").strip()
        if not job_description:
            return jsonify({"error": "Campo 'jobDescription' é obrigatório."}), 400
        candidates = _fetch_otw_candidates()
        result = _call_openai_for_candidate_matches(job_description, candidates)
        if "matches" not in result:
            result = {"matches": []}
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": "Erro interno ao processar o match.", "detail": str(exc)}), 500


def _find_col(header, must_contain, exclude=None):
    exclude = exclude or []
    for idx, cell in enumerate(header):
        cell_lower = (cell or "").strip().lower()
        if any(term in cell_lower for term in must_contain) and not any(ex in cell_lower for ex in exclude):
            return idx
    return -1


def _fetch_otw_candidates():
    req = _Request(_SHEET_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with _urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    rows = list(_csv.reader(_io.StringIO(raw)))
    header_idx = -1
    for i in range(min(len(rows), 10)):
        if any((c or "").strip().lower() == "nome" for c in rows[i]):
            header_idx = i
            break
    if header_idx == -1:
        return []

    header = rows[header_idx]
    col = {
        "nome": _find_col(header, ["nome"], ["sobrenome"]),
        "senioridade": _find_col(header, ["senioridade"]),
        "area": _find_col(header, ["área de atua", "area de atua"]),
        "ferramentas": _find_col(header, ["ferramenta"]),
        "local": _find_col(header, ["localiza"]),
        "condicao": _find_col(header, ["condição de trabalho", "condicao de trabalho"]),
        "whatsapp": _find_col(header, ["whatsapp"], ["clic"]),
        "exp": _find_col(header, ["tempo de experi"]),
    }

    candidates = []
    for r in rows[header_idx + 1:]:
        if col["nome"] < 0 or col["nome"] >= len(r) or not (r[col["nome"]] or "").strip():
            continue
        candidates.append({
            "name": (r[col["nome"]] or "").strip(),
            "seniority": (r[col["senioridade"]] or "").strip() if 0 <= col["senioridade"] < len(r) else "",
            "city": (r[col["local"]] or "").strip() if 0 <= col["local"] < len(r) else "",
            "workModel": (r[col["condicao"]] or "").strip() if 0 <= col["condicao"] < len(r) else "",
            "skills": (r[col["ferramentas"]] or "").strip() if 0 <= col["ferramentas"] < len(r) else "",
            "experience": (r[col["exp"]] or "").strip() if 0 <= col["exp"] < len(r) else "",
            "whatsapp": _re.sub(r"\\D", "", r[col["whatsapp"]] or "") if 0 <= col["whatsapp"] < len(r) else "",
        })

    return candidates[:_MAX_CANDIDATES_TO_SEND]


def _call_openai_for_candidate_matches(job_description, candidates):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada nas variáveis de ambiente da Vercel.")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "Você é um recrutador especialista em CRM, CX e RevOps no Brasil. "
        "Receberá a descrição de uma vaga e uma lista de candidatos (nome, cidade, "
        "senioridade, modelo de trabalho, ferramentas/skills, experiência). "
        "Retorne SOMENTE um JSON válido, sem texto fora do JSON, no formato: "
        '{"matches": [{"name": "...", "city": "...", "seniority": "...", '
        '"workModel": "...", "matchScore": 0-100, "matchedSkills": ["..."], '
        '"matchReason": "frase curta explicando o motivo do match", '
        '"whatsapp": "..."}]}. '
        f"Retorne no máximo {_MAX_RESULTS} candidatos, ordenados do maior para o "
        "menor matchScore. Só inclua candidatos com aderência real à vaga."
    )
    user_prompt = json.dumps({"jobDescription": job_description, "candidates": candidates}, ensure_ascii=False)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return json.loads(completion.choices[0].message.content)


@app.route("/api/match-freelancers", methods=["POST", "OPTIONS"])
def match_freelancers():
    if request.method == "OPTIONS":
        return "", 204
    try:
        body = request.get_json(force=True, silent=True) or {}
        challenge = (body.get("challenge") or "").strip()
        if not challenge:
            return jsonify({"error": "Campo 'challenge' é obrigatório."}), 400
        matches = _call_supabase_match_freelancers(challenge)
        return jsonify({"matches": matches}), 200
    except Exception as exc:
        return jsonify({"error": "Erro interno ao buscar freelancers.", "detail": str(exc)}), 500


def _call_supabase_match_freelancers(challenge_text):
    url = f"{_SUPABASE_URL_MATCH}/rest/v1/rpc/match_freelancers"
    payload = json.dumps({"challenge_text": challenge_text}).encode("utf-8")
    req = _Request(url, data=payload, method="POST", headers={
        "Content-Type": "application/json",
        "apikey": _SUPABASE_ANON_KEY_MATCH,
        "Authorization": f"Bearer {_SUPABASE_ANON_KEY_MATCH}",
    })
    with _urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


@app.route("/api/match-platforms", methods=["POST", "OPTIONS"])
def match_platforms():
    if request.method == "OPTIONS":
        return "", 204
    try:
        body = request.get_json(force=True, silent=True) or {}
        challenge = (body.get("challenge") or "").strip()
        platforms = body.get("platforms") or []
        if not challenge:
            return jsonify({"error": "Campo 'challenge' é obrigatório."}), 400
        if not platforms:
            return jsonify({"matches": []}), 200

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY não configurada.")

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        system_prompt = (
            "Você é um especialista em ecossistema de CRM e Martech no Brasil. "
            "Receberá a descrição de um desafio de negócio e uma lista de plataformas "
            "(nome, categoria, tags). Retorne SOMENTE JSON válido no formato: "
            '{"matches": [{"name": "...", "cat": "...", "matchScore": 0-100, '
            '"matchedTags": ["..."], "matchReason": "frase curta", "site": "..."}]}. '
            "Retorne no máximo 5 plataformas, ordenadas por matchScore. "
            "Só inclua plataformas com aderência real ao desafio."
        )
        user_prompt = json.dumps({
            "challenge": challenge,
            "platforms": [{"name": p.get("name", ""), "cat": p.get("cat", ""), "tags": p.get("tags", [])} for p in platforms],
        }, ensure_ascii=False)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        result = json.loads(completion.choices[0].message.content)
        site_map = {p.get("name", ""): p.get("site", "") for p in platforms}
        for m in result.get("matches", []):
            if not m.get("site"):
                m["site"] = site_map.get(m.get("name", ""), "")
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": "Erro interno.", "detail": str(exc)}), 500
'''

if __name__ == "__main__":
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    if "def match_candidates" in content:
        print("AVISO: match_candidates ja existe no app.py")
    else:
        content += MATCH_ROUTES_CODE
        with open("app.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("OK: 3 rotas de Match por IA adicionadas ao app.py")

    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            reqs = f.read()
    except FileNotFoundError:
        reqs = ""

    if "openai" not in reqs.lower():
        with open("requirements.txt", "a", encoding="utf-8") as f:
            f.write("\nopenai>=1.0.0\n")
        print("OK: openai adicionado ao requirements.txt")
    else:
        print("INFO: openai ja estava no requirements.txt")
