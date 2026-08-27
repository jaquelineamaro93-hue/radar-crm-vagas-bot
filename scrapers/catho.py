"""
Scraper para Catho.com.br — focado em CRM.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Catho"
BASE_URL = "https://www.catho.com.br"

SEARCHES = [
    "crm-copywriter",
    "lifecycle-copywriter",
    "redator-de-ciclo-de-vida",
    "growth-copywriter",
    "growth-writer",
    "copywriter-de-inbound-e-automacao",
    "copywriter-de-mensageria-e-conversao",
    "copywriter-whatsapp-push-sms",
    "copywriter-de-revops",
    "copywriter-sales-enablement",
    "conversational-copywriter",
    "redator-para-agentes-de-ia-e-bots",
    "email-marketing-copywriter",
    "ux-writer-microcopy",
    "ux-writer-jornadas",
    "ux-writer-reguas",
    "crm-designer",
    "lifecycle-designer",
    "designer-de-relacionamento",
    "growth-designer",
    "designer-de-automacao-de-marketing",
    "email-marketing-designer",
    "designer-html-css-email",
    "designer-de-canais-proprietarios",
    "designer-owned-media",
    "designer-whatsapp-push-in-app",
    "visual-designer-retencao",
    "visual-designer-ltv",
    "martech-visual-specialist",
    "designer-braze-insider",
    "ui-designer-jornadas-de-clientes",
    "designer-de-ciclo-de-vida",
    "designer-de-growth-e-retencao",
    "designer-para-plataformas-de-automacao",
    "designer-rd-station-braze-insider",
    "designer-programas-de-fidelidade",
    "creative-growth-specialist",
    "especialista-de-criacao-para-growth",
    "conversational-experience-designer",
    "especialista-de-conteudo-hubspot-rd-station",
    "braze-content-specialist",
    "insider-content-specialist",
    "revops-creative-specialist",
    "creative-operations-specialist-martech",
    "especialista-em-criacao-e-design-regua-de-relacionamento",
    "especialista-em-operacoes-criativas-martech",
    "redator-de-crm",
    "redator-de-crm-marketing",
    "redator-lifecycle",
    "copywriter-de-retencao-e-nutricao",
    "copywriter-inbound-rd-station-hubspot",
    "redator-de-mensageria-whatsapp-sms-push",
    "redator-revops-cadencias-de-vendas",
    "redator-de-email-marketing",
    "redator-regua-de-relacionamento",
    "redator-conversacional-bots",
    "designer-de-experiencia-conversacional",
    "especialista-em-conteudo-e-prompting-ia-crm",
    "arquiteto-de-fluxos-conversacionais",
    "designer-fluxos-whatsapp-kommo",
    "salesforce-marketing-cloud-specialist",
    "salesforce-marketing-cloud-developer",
    "salesforce-marketing-cloud-architect",
    "marketing-cloud-consultant",
    "marketing-cloud-email-specialist",
    "forward-deployed-engineer",
    "fde-ai-martech",
    "ai-agent-architect",
    "ai-agent-product-manager",
    "ai-solutions-architect-crm",
    "desenvolvedor-de-agentes-de-ia",
    "engenheiro-de-integracao-de-agentes",
    "especialista-em-crm-e-inteligencia-artificial",
    "ai-lifecycle-marketing",
    "crm-preditivo",
    "predictive-crm-specialist",
    "ai-driven-growth-specialist",
    "analista-de-dados-de-crm-machine-learning",
    "real-time-personalization-specialist",
    "ia-conversacional",
    "conversational-ai-specialist",
    "prompt-engineer-crm",
    "prompt-engineer-cx",
    "conversational-ai-product-owner",
    "automacao-de-atendimento-ia-generativa",
    "arquiteto-de-bots-agentes-autonomos",
    "ai-martech-operations-specialist",
    "cdp-ai-data-specialist",
    "orquestracao-de-agentes-crm",
    "engenheiro-de-dados-de-consumidor-ia",
    "head-of-ai-customer-experience",
    "head-of-ai-driven-crm",
    "tech-lead-agentes-de-ia",
    "gerente-de-agentes-de-ia",
    "lifecycle-marketing-specialist",
    "lifecycle-marketing-manager",
    "retention-marketing-specialist",
    "retention-marketing-manager",
    "especialista-em-engajamento-e-reativacao",
    "especialista-de-prevencao-a-churn",
    "churn-specialist",
    "customer-marketing-specialist",
    "customer-marketing-manager",
    "monetizacao-de-base",
    "marketing-automation-specialist",
    "marketing-automation-architect",
    "especialista-de-martech",
    "analista-de-martech",
    "marketing-operations-analyst",
    "marketing-operations-manager",
    "marketing-ops",
    "arquiteto-de-solucoes-de-marketing",
    "growth-marketing-manager",
    "growth-marketing-specialist",
    "retention-growth-manager",
    "ltv-specialist",
    "ltv-manager",
    "product-growth-analyst",
    "especialista-em-canais-proprietarios",
    "owned-media-specialist",
    "inbound-marketing-specialist",
    "inbound-marketing-manager",
    "messaging-push-notification-specialist",
    "email-marketing-manager",
    "analista-de-mensageria-whatsapp",
    "loyalty-specialist",
    "loyalty-manager",
    "especialista-em-programas-de-fidelidade",
    "gerente-de-programas-de-fidelidade",
    "customer-journey-specialist",
    "customer-journey-manager",
    "especialista-de-mapeamento-de-jornada",
    "customer-experience-specialist",
    "customer-experience-manager",
    "analista-de-voc-voice-of-customer",
    "analista-de-nps",
    "cdp-specialist",
    "customer-data-platform-specialist",
    "customer-data-analyst",
    "customer-intelligence-specialist",
    "database-marketing-analyst",
    "analista-de-segmentacao-consumidor",
    "martech-data-specialist",
    "product-manager-martech",
    "product-manager-lifecycle",
    "product-manager-growth",
    "product-owner-plataformas-de-marketing",
    "analista-de-crm-marketing",
    "analista-de-marketing-de-relacionamento",
    "analista-de-regua-de-relacionamento",
    "analista-de-automacao-de-marketing",
    "analista-de-inbound-marketing",
    "analista-de-lifecycle-marketing",
    "analista-de-retencao-e-engajamento",
    "growth-crm-specialist",
    "retention-specialist",
    "especialista-em-crm-e-ltv",
    "analista-de-crm-data-analytics",
    "analista-de-operacoes-de-crm",
    "crm-ops",
    "especialista-de-growth-e-lifecycle",
    "especialista-de-canais-digitais",
    "digital-channels-specialist",
    "analista-de-programas-de-fidelidade",
    "especialista-em-customer-experience-e-crm",
    "analista-de-omnichannel",
    "coordenador-de-crm-e-growth",
    "coordenador-de-lifecycle-marketing",
    "coordenador-de-marketing-de-relacionamento",
    "gerente-de-crm-e-martech",
    "gerente-de-lifecycle-e-retention",
    "head-de-crm-e-growth",
    "head-de-customer-marketing",
    "head-de-lifecycle-martech",
    "diretor-de-crm-e-customer-experience",
    "crm-lifecycle-marketing-manager",
    "customer-retention-specialist",
    "crm-operations-manager",
    "crm-data-analyst",
    "crm-product-owner",
    "crm", "salesforce", "hubspot", "rd-station",
    "crm-marketing", "marketing-de-relacionamento",
    "marketing-automation", "analista-de-campanhas",
    "braze", "klaviyo", "pipedrive",
]

def scrape() -> list[dict]:
    vagas = []
    seen = set()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    for q in SEARCHES:
        try:
            url = f"{BASE_URL}/vagas/home-office/?q={q}"
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("article, div[class*='JobCard'], div[class*='job-card'], li[class*='job']")
            for card in cards:
                title_el = card.select_one("h2, h3, [class*='title'], [class*='Title'], [class*='name']")
                link_el = card.select_one("a[href]")
                if not title_el or not link_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue
                href = link_el.get("href", "")
                url_vaga = f"{BASE_URL}{href}" if href.startswith("/") else href
                if url_vaga in seen:
                    continue
                seen.add(url_vaga)
                category = classify(title)
                if not category:
                    continue
                company_el = card.select_one("[class*='company'], [class*='Company'], [class*='employer']")
                company = company_el.get_text(strip=True) if company_el else "Não informado"
                vagas.append({
                    "title": title,
                    "company": company,
                    "url": url_vaga,
                    "location": "Remoto",
                    "description": "",
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[Catho] Erro '{q}': {e}")
    print(f"[Catho] {len(vagas)} vagas encontradas")
    return vagas
