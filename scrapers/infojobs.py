"""
Scraper para InfoJobs.com.br — board com 20 vagas por página.
Requer Accept-Encoding: identity para evitar brotli (não suportado pelo requests).
Datas em formato '2026/04/28 01:53:00' no atributo data-value.
"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from .base import classify

_AUTOMATION_CATS = {"automacao_presencial", "automacao_remote"}
SOURCE = "InfoJobs"
BASE_URL = "https://www.infojobs.com.br"

# (slug, remote_only, forced_category_or_None)
SEARCHES = [
    ("vagas-de-emprego-crm-copywriter-trabalho-home-office", True, None),
    ("vagas-de-emprego-lifecycle-copywriter-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-de-ciclo-de-vida-trabalho-home-office", True, None),
    ("vagas-de-emprego-growth-copywriter-trabalho-home-office", True, None),
    ("vagas-de-emprego-growth-writer-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-de-inbound-e-automacao-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-de-mensageria-e-conversao-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-whatsapp-push-sms-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-de-revops-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-sales-enablement-trabalho-home-office", True, None),
    ("vagas-de-emprego-conversational-copywriter-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-para-agentes-de-ia-e-bots-trabalho-home-office", True, None),
    ("vagas-de-emprego-email-marketing-copywriter-trabalho-home-office", True, None),
    ("vagas-de-emprego-ux-writer-microcopy-trabalho-home-office", True, None),
    ("vagas-de-emprego-ux-writer-jornadas-trabalho-home-office", True, None),
    ("vagas-de-emprego-ux-writer-reguas-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-designer-trabalho-home-office", True, None),
    ("vagas-de-emprego-lifecycle-designer-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-growth-designer-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-de-automacao-de-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-email-marketing-designer-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-html-css-email-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-de-canais-proprietarios-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-owned-media-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-whatsapp-push-in-app-trabalho-home-office", True, None),
    ("vagas-de-emprego-visual-designer-retencao-trabalho-home-office", True, None),
    ("vagas-de-emprego-visual-designer-ltv-trabalho-home-office", True, None),
    ("vagas-de-emprego-martech-visual-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-braze-insider-trabalho-home-office", True, None),
    ("vagas-de-emprego-ui-designer-jornadas-de-clientes-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-de-ciclo-de-vida-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-de-growth-e-retencao-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-para-plataformas-de-automacao-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-rd-station-braze-insider-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-programas-de-fidelidade-trabalho-home-office", True, None),
    ("vagas-de-emprego-creative-growth-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-criacao-para-growth-trabalho-home-office", True, None),
    ("vagas-de-emprego-conversational-experience-designer-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-conteudo-hubspot-rd-station-trabalho-home-office", True, None),
    ("vagas-de-emprego-braze-content-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-insider-content-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-revops-creative-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-creative-operations-specialist-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-criacao-e-design-regua-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-operacoes-criativas-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-de-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-de-crm-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-lifecycle-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-de-retencao-e-nutricao-trabalho-home-office", True, None),
    ("vagas-de-emprego-copywriter-inbound-rd-station-hubspot-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-de-mensageria-whatsapp-sms-push-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-revops-cadencias-de-vendas-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-de-email-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-regua-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-redator-conversacional-bots-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-de-experiencia-conversacional-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-conteudo-e-prompting-ia-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-arquiteto-de-fluxos-conversacionais-trabalho-home-office", True, None),
    ("vagas-de-emprego-designer-fluxos-whatsapp-kommo-trabalho-home-office", True, None),
    ("vagas-de-emprego-salesforce-marketing-cloud-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-salesforce-marketing-cloud-developer-trabalho-home-office", True, None),
    ("vagas-de-emprego-salesforce-marketing-cloud-architect-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-cloud-consultant-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-cloud-email-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-forward-deployed-engineer-trabalho-home-office", True, None),
    ("vagas-de-emprego-fde-ai-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-ai-agent-architect-trabalho-home-office", True, None),
    ("vagas-de-emprego-ai-agent-product-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-ai-solutions-architect-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-desenvolvedor-de-agentes-de-ia-trabalho-home-office", True, None),
    ("vagas-de-emprego-engenheiro-de-integracao-de-agentes-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-crm-e-inteligencia-artificial-trabalho-home-office", True, None),
    ("vagas-de-emprego-ai-lifecycle-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-preditivo-trabalho-home-office", True, None),
    ("vagas-de-emprego-predictive-crm-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-ai-driven-growth-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-dados-de-crm-machine-learning-trabalho-home-office", True, None),
    ("vagas-de-emprego-real-time-personalization-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-ia-conversacional-trabalho-home-office", True, None),
    ("vagas-de-emprego-conversational-ai-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-prompt-engineer-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-prompt-engineer-cx-trabalho-home-office", True, None),
    ("vagas-de-emprego-conversational-ai-product-owner-trabalho-home-office", True, None),
    ("vagas-de-emprego-automacao-de-atendimento-ia-generativa-trabalho-home-office", True, None),
    ("vagas-de-emprego-arquiteto-de-bots-agentes-autonomos-trabalho-home-office", True, None),
    ("vagas-de-emprego-ai-martech-operations-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-cdp-ai-data-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-orquestracao-de-agentes-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-engenheiro-de-dados-de-consumidor-ia-trabalho-home-office", True, None),
    ("vagas-de-emprego-head-of-ai-customer-experience-trabalho-home-office", True, None),
    ("vagas-de-emprego-head-of-ai-driven-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-tech-lead-agentes-de-ia-trabalho-home-office", True, None),
    ("vagas-de-emprego-gerente-de-agentes-de-ia-trabalho-home-office", True, None),
    ("vagas-de-emprego-lifecycle-marketing-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-lifecycle-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-retention-marketing-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-retention-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-engajamento-e-reativacao-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-prevencao-a-churn-trabalho-home-office", True, None),
    ("vagas-de-emprego-churn-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-marketing-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-monetizacao-de-base-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-automation-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-automation-architect-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-operations-analyst-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-operations-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-ops-trabalho-home-office", True, None),
    ("vagas-de-emprego-arquiteto-de-solucoes-de-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-growth-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-growth-marketing-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-retention-growth-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-ltv-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-ltv-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-product-growth-analyst-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-canais-proprietarios-trabalho-home-office", True, None),
    ("vagas-de-emprego-owned-media-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-inbound-marketing-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-inbound-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-messaging-push-notification-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-email-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-mensageria-whatsapp-trabalho-home-office", True, None),
    ("vagas-de-emprego-loyalty-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-loyalty-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-programas-de-fidelidade-trabalho-home-office", True, None),
    ("vagas-de-emprego-gerente-de-programas-de-fidelidade-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-journey-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-journey-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-mapeamento-de-jornada-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-experience-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-experience-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-voc-voice-of-customer-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-nps-trabalho-home-office", True, None),
    ("vagas-de-emprego-cdp-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-data-platform-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-data-analyst-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-intelligence-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-database-marketing-analyst-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-segmentacao-consumidor-trabalho-home-office", True, None),
    ("vagas-de-emprego-martech-data-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-product-manager-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-product-manager-lifecycle-trabalho-home-office", True, None),
    ("vagas-de-emprego-product-manager-growth-trabalho-home-office", True, None),
    ("vagas-de-emprego-product-owner-plataformas-de-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-crm-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-marketing-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-regua-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-automacao-de-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-inbound-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-lifecycle-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-retencao-e-engajamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-growth-crm-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-retention-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-crm-e-ltv-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-crm-data-analytics-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-operacoes-de-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-ops-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-growth-e-lifecycle-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-de-canais-digitais-trabalho-home-office", True, None),
    ("vagas-de-emprego-digital-channels-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-programas-de-fidelidade-trabalho-home-office", True, None),
    ("vagas-de-emprego-especialista-em-customer-experience-e-crm-trabalho-home-office", True, None),
    ("vagas-de-emprego-analista-de-omnichannel-trabalho-home-office", True, None),
    ("vagas-de-emprego-coordenador-de-crm-e-growth-trabalho-home-office", True, None),
    ("vagas-de-emprego-coordenador-de-lifecycle-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-coordenador-de-marketing-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-gerente-de-crm-e-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-gerente-de-lifecycle-e-retention-trabalho-home-office", True, None),
    ("vagas-de-emprego-head-de-crm-e-growth-trabalho-home-office", True, None),
    ("vagas-de-emprego-head-de-customer-marketing-trabalho-home-office", True, None),
    ("vagas-de-emprego-head-de-lifecycle-martech-trabalho-home-office", True, None),
    ("vagas-de-emprego-diretor-de-crm-e-customer-experience-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-lifecycle-marketing-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-customer-retention-specialist-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-operations-manager-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-data-analyst-trabalho-home-office", True, None),
    ("vagas-de-emprego-crm-product-owner-trabalho-home-office", True, None),
    # CRM genérico
    ("vagas-de-emprego-analista-de-crm-trabalho-home-office",           True, None),
    ("vagas-de-emprego-especialista-em-crm-trabalho-home-office",       True, None),
    ("vagas-de-emprego-coordenador-de-crm-trabalho-home-office",        True, None),
    ("vagas-de-emprego-gerente-de-crm-trabalho-home-office",            True, None),
    ("vagas-de-emprego-diretor-de-crm-trabalho-home-office",            True, None),
    ("vagas-de-emprego-consultor-de-crm-trabalho-home-office",          True, None),
    ("vagas-de-emprego-crm-trabalho-home-office",                       True, None),
    # CRM Marketing
    ("vagas-de-emprego-crm-marketing-trabalho-home-office",             True, None),
    ("vagas-de-emprego-marketing-de-relacionamento-trabalho-home-office", True, None),
    ("vagas-de-emprego-marketing-automation-trabalho-home-office",      True, None),
    ("vagas-de-emprego-lifecycle-marketing-trabalho-home-office",       True, None),
    ("vagas-de-emprego-analista-de-campanhas-trabalho-home-office",     True, None),
    # Salesforce
    ("vagas-de-emprego-salesforce-trabalho-home-office",                True, None),
    ("vagas-de-emprego-analista-de-salesforce-trabalho-home-office",    True, None),
    ("vagas-de-emprego-salesforce-developer-trabalho-home-office",      True, None),
    ("vagas-de-emprego-salesforce-administrator-trabalho-home-office",  True, None),
    ("vagas-de-emprego-salesforce-consultant-trabalho-home-office",     True, None),
    ("vagas-de-emprego-marketing-cloud-trabalho-home-office",           True, None),
    # HubSpot
    ("vagas-de-emprego-hubspot-trabalho-home-office",                   True, None),
    ("vagas-de-emprego-analista-de-hubspot-trabalho-home-office",       True, None),
    # RD Station
    ("vagas-de-emprego-rd-station-trabalho-home-office",                True, None),
    # Outras plataformas
    ("vagas-de-emprego-dynamics-crm-trabalho-home-office",              True, None),
    ("vagas-de-emprego-pipedrive-trabalho-home-office",                 True, None),
    ("vagas-de-emprego-activecampaign-trabalho-home-office",            True, None),
    ("vagas-de-emprego-braze-trabalho-home-office",                     True, None),
    ("vagas-de-emprego-klaviyo-trabalho-home-office",                   True, None),
]


def _parse_date(raw: str) -> str | None:
    """Converte '2026/04/28 01:53:00' para ISO 8601."""
    raw = raw.strip()
    try:
        dt = datetime.strptime(raw, "%Y/%m/%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _clean_company(el) -> str:
    """Texto da empresa sem ícones SVG embutidos."""
    if not el:
        return "Não informado"
    for tag in el.find_all(["svg", "i", "span"]):
        tag.decompose()
    return el.get_text(strip=True) or "Não informado"


def scrape() -> list[dict]:
    vagas: list[dict] = []
    seen_ids: set[str] = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
        # identity evita brotli — requests não sabe decodificar br
        "Accept-Encoding": "identity",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    for slug, _remote, forced_cat in SEARCHES:
        url = f"{BASE_URL}/{slug}.aspx"
        try:
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_="js_vacancyLoad")

            for card in cards:
                vaga_id   = card.get("data-id", "")
                data_href = card.get("data-href", "")
                if not vaga_id or vaga_id in seen_ids:
                    continue
                seen_ids.add(vaga_id)

                title_el  = card.find("h2")
                date_el   = card.find("div", class_="js_date")
                comp_link = card.find("a", href=re.compile(r"/empresa-"))
                loc_el    = card.find("div", class_="mb-8")

                title        = title_el.get_text(strip=True) if title_el else ""
                company      = _clean_company(comp_link)
                location     = loc_el.get_text(strip=True) if loc_el else ("Remoto" if _remote else "Presencial")
                raw_date     = (date_el.get("data-value") or "") if date_el else ""
                published_at = _parse_date(raw_date) if raw_date else None
                full_url     = f"{BASE_URL}{data_href}" if data_href else ""

                if not title or not full_url:
                    continue

                if forced_cat:
                    # Para categorias de automação, valida o título mesmo com forced_cat
                    if forced_cat in _AUTOMATION_CATS and classify(title) not in _AUTOMATION_CATS:
                        continue
                    category = forced_cat
                else:
                    category = classify(title)
                    if not category:
                        continue

                vagas.append({
                    "title":        title,
                    "company":      company,
                    "url":          full_url,
                    "location":     location,
                    "description":  "",
                    "source":       SOURCE,
                    "category":     category,
                    "published_at": published_at,
                })

        except Exception as e:
            print(f"[InfoJobs] {slug}: {e}")

    print(f"[InfoJobs] {len(vagas)} vagas encontradas")
    return vagas
