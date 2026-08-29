import requests
# Discord removido
from scrapers.base import format_date, extract_seniority

CATEGORY_COLORS = {
    "designer":              0x5865F2,   # índigo Discord
    "cxcs":                  0x57F287,   # verde Discord
    "automacao_presencial":  0xED4245,   # vermelho Discord
    "automacao_remote":      0xFEE75C,   # amarelo Discord
    "dev":                   0x3498DB,   # azul
    "edfis":                 0x2ECC71,   # verde esmeralda
    "crm":                   0xE67E22,   # laranja
    "data":                  0x9B59B6,   # roxo
    "po_pm":                 0x1ABC9C,   # turquesa
    "qa":                    0xF39C12,   # âmbar
}

CATEGORY_EMOJIS = {
    "designer":             "🎨",
    "cxcs":                 "🤝",
    "automacao_presencial": "🏭",
    "automacao_remote":     "⚙️",
    "dev":                  "💻",
    "edfis":                "🏋️",
    "crm":                  "📊",
    "data":                 "🗄️",
    "po_pm":                "🎯",
    "qa":                   "🔍",
}

CATEGORY_MODELO = {
    "designer":             "Remoto",
    "cxcs":                 "Remoto",
    "automacao_presencial": "Presencial",
    "automacao_remote":     "Remoto",
    "dev":                  "Remoto",
    "edfis":                "SP / Remoto",
    "crm":                  "Remoto",
    "data":                 "Remoto",
    "po_pm":                "Remoto",
    "qa":                   "Remoto",
}

SOURCE_ICONS = {
    "linkedin":      "🔵",
    "vagasremotas":  "🌐",
    "indeed":        "🟦",
    "behance":       "💼",
    "dribbble":      "🏀",
    "inhire":        "🟣",
    "gupy":          "🟠",
    "remotar":       "🔆",
    "trampos":       "🟡",
    "programathor":  "⚡",
    "vagas.com":     "🇧🇷",
    "infojobs":      "📋",
    "nerdin":        "🖥️",
    "empregos.com":  "🟢",
    "indeed":        "🔷",
    "dribbble":      "🏀",
    "trampos":       "🟡",
}


def _get_webhooks(category: str) -> list[str]:
    """Retorna lista de webhooks para a categoria (suporte a múltiplos destinos)."""
    if category in ("automacao_presencial", "automacao_remote"):
        return [w for w in [DISCORD_WEBHOOK_AUTOMACAO] if w]
    if category == "designer":
        return [w for w in [DISCORD_WEBHOOK_DESIGNER, DISCORD_WEBHOOK_DESIGNER_2] if w]
    if category == "cxcs":
        return [w for w in [DISCORD_WEBHOOK_CXCS] if w]
    if category == "dev":
        return [w for w in [DISCORD_WEBHOOK_DEV] if w]
    if category == "edfis":
        return [w for w in [DISCORD_WEBHOOK_EDFIS] if w]
    if category == "crm":
        return [w for w in [DISCORD_WEBHOOK_CRM] if w]
    if category == "data":
        return [w for w in [DISCORD_WEBHOOK_DATA] if w]
    if category == "po_pm":
        return [w for w in [DISCORD_WEBHOOK_POPM] if w]
    if category == "qa":
        return [w for w in [DISCORD_WEBHOOK_QA] if w]
    return [w for w in [DISCORD_WEBHOOK_URL] if w]


def send_vaga_disabled(vaga: dict):
    webhooks = _get_webhooks(vaga.get("category", ""))
    if not webhooks:
        print("[WARN] Nenhum webhook configurado.")
        return

    category  = vaga.get("category", "")
    source    = vaga.get("source", "").lower()
    title     = vaga.get("title", "Sem título")
    company   = vaga.get("company", "Empresa não informada") or "Não informado"
    location  = vaga.get("location", "") or ""
    url       = vaga.get("url", "")
    desc      = vaga.get("description", "") or ""
    pub_at    = vaga.get("published_at")

    source_icon = SOURCE_ICONS.get(source, "📌")
    cat_emoji   = CATEGORY_EMOJIS.get(category, "💼")
    color       = CATEGORY_COLORS.get(category, 0xFEE75C)
    date_label  = format_date(pub_at)
    seniority   = extract_seniority(title)
    modelo      = CATEGORY_MODELO.get(category, "Remoto")

    company  = (company.strip() or "Não informado")[:256]
    location = (location.strip() or modelo)[:256]
    # Limites Discord: title ≤256, field value ≤1024, total embed ≤6000
    title_safe = f"{cat_emoji} {title}"[:256]

    fields = [
        {"name": "🏢 Empresa",   "value": company,    "inline": True},
        {"name": "📍 Local",     "value": location,   "inline": True},
        {"name": "📅 Publicada", "value": date_label, "inline": True},
        {"name": f"{source_icon} Fonte", "value": (vaga.get("source") or "—")[:256], "inline": True},
        {"name": "🖥️ Modelo",   "value": modelo[:256], "inline": True},
    ]

    if seniority:
        fields.append({"name": "📊 Nível", "value": seniority[:256], "inline": True})

    if desc:
        snippet = desc[:900].strip()
        # Remove tags HTML simples (Gupy retorna HTML)
        import re as _re
        snippet = _re.sub(r"<[^>]+>", " ", snippet)
        snippet = _re.sub(r"\s+", " ", snippet).strip()
        if len(snippet) > 20:
            if len(desc) > 900:
                snippet += "..."
            fields.append({"name": "📝 Sobre a vaga", "value": snippet[:1024], "inline": False})

    # Discord exige URL absoluta no embed; URL relativa ou inválida → HTTP 400
    safe_url = url if url and url.startswith(("http://", "https://")) else None

    embed = {
        "title": title_safe,
        "color": color,
        "fields": fields,
        "footer": {
            "text": "Bot de Vagas • Dev & Design & CX/CS & Automação"
        },
    }
    if safe_url:
        embed["url"] = safe_url

    for webhook_url in webhooks:
        try:
            resp = requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
            if not resp.ok:
                print(f"[ERROR] Discord HTTP {resp.status_code} ({webhook_url[:50]}…): {resp.text[:300]}")
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERROR] Discord ({webhook_url[:50]}…): {e}")
