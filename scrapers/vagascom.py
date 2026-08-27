"""
Scraper para Vagas.com.br — focado em CRM.
Usa o atributo title= do link para pegar o título correto.
"""
import requests
from bs4 import BeautifulSoup
from .base import classify

SOURCE = "Vagas.com"
BASE_URL = "https://www.vagas.com.br"

SEARCHES = [
    "vagas-de-crm-copywriter",
    "vagas-de-lifecycle-copywriter",
    "vagas-de-redator-de-ciclo-de-vida",
    "vagas-de-growth-copywriter",
    "vagas-de-growth-writer",
    "vagas-de-copywriter-de-inbound-e-automacao",
    "vagas-de-copywriter-de-mensageria-e-conversao",
    "vagas-de-copywriter-whatsapp-push-sms",
    "vagas-de-copywriter-de-revops",
    "vagas-de-copywriter-sales-enablement",
    "vagas-de-conversational-copywriter",
    "vagas-de-redator-para-agentes-de-ia-e-bots",
    "vagas-de-email-marketing-copywriter",
    "vagas-de-ux-writer-microcopy",
    "vagas-de-ux-writer-jornadas",
    "vagas-de-ux-writer-reguas",
    "vagas-de-crm-designer",
    "vagas-de-lifecycle-designer",
    "vagas-de-designer-de-relacionamento",
    "vagas-de-growth-designer",
    "vagas-de-designer-de-automacao-de-marketing",
    "vagas-de-email-marketing-designer",
    "vagas-de-designer-html-css-email",
    "vagas-de-designer-de-canais-proprietarios",
    "vagas-de-designer-owned-media",
    "vagas-de-designer-whatsapp-push-in-app",
    "vagas-de-visual-designer-retencao",
    "vagas-de-visual-designer-ltv",
    "vagas-de-martech-visual-specialist",
    "vagas-de-designer-braze-insider",
    "vagas-de-ui-designer-jornadas-de-clientes",
    "vagas-de-designer-de-ciclo-de-vida",
    "vagas-de-designer-de-growth-e-retencao",
    "vagas-de-designer-para-plataformas-de-automacao",
    "vagas-de-designer-rd-station-braze-insider",
    "vagas-de-designer-programas-de-fidelidade",
    "vagas-de-creative-growth-specialist",
    "vagas-de-especialista-de-criacao-para-growth",
    "vagas-de-conversational-experience-designer",
    "vagas-de-especialista-de-conteudo-hubspot-rd-station",
    "vagas-de-braze-content-specialist",
    "vagas-de-insider-content-specialist",
    "vagas-de-revops-creative-specialist",
    "vagas-de-creative-operations-specialist-martech",
    "vagas-de-especialista-em-criacao-e-design-regua-de-relacionamento",
    "vagas-de-especialista-em-operacoes-criativas-martech",
    "vagas-de-redator-de-crm",
    "vagas-de-redator-de-crm-marketing",
    "vagas-de-redator-lifecycle",
    "vagas-de-copywriter-de-retencao-e-nutricao",
    "vagas-de-copywriter-inbound-rd-station-hubspot",
    "vagas-de-redator-de-mensageria-whatsapp-sms-push",
    "vagas-de-redator-revops-cadencias-de-vendas",
    "vagas-de-redator-de-email-marketing",
    "vagas-de-redator-regua-de-relacionamento",
    "vagas-de-redator-conversacional-bots",
    "vagas-de-designer-de-experiencia-conversacional",
    "vagas-de-especialista-em-conteudo-e-prompting-ia-crm",
    "vagas-de-arquiteto-de-fluxos-conversacionais",
    "vagas-de-designer-fluxos-whatsapp-kommo",
    "vagas-de-salesforce-marketing-cloud-specialist",
    "vagas-de-salesforce-marketing-cloud-developer",
    "vagas-de-salesforce-marketing-cloud-architect",
    "vagas-de-marketing-cloud-consultant",
    "vagas-de-marketing-cloud-email-specialist",
    "vagas-de-forward-deployed-engineer",
    "vagas-de-fde-ai-martech",
    "vagas-de-ai-agent-architect",
    "vagas-de-ai-agent-product-manager",
    "vagas-de-ai-solutions-architect-crm",
    "vagas-de-desenvolvedor-de-agentes-de-ia",
    "vagas-de-engenheiro-de-integracao-de-agentes",
    "vagas-de-especialista-em-crm-e-inteligencia-artificial",
    "vagas-de-ai-lifecycle-marketing",
    "vagas-de-crm-preditivo",
    "vagas-de-predictive-crm-specialist",
    "vagas-de-ai-driven-growth-specialist",
    "vagas-de-analista-de-dados-de-crm-machine-learning",
    "vagas-de-real-time-personalization-specialist",
    "vagas-de-ia-conversacional",
    "vagas-de-conversational-ai-specialist",
    "vagas-de-prompt-engineer-crm",
    "vagas-de-prompt-engineer-cx",
    "vagas-de-conversational-ai-product-owner",
    "vagas-de-automacao-de-atendimento-ia-generativa",
    "vagas-de-arquiteto-de-bots-agentes-autonomos",
    "vagas-de-ai-martech-operations-specialist",
    "vagas-de-cdp-ai-data-specialist",
    "vagas-de-orquestracao-de-agentes-crm",
    "vagas-de-engenheiro-de-dados-de-consumidor-ia",
    "vagas-de-head-of-ai-customer-experience",
    "vagas-de-head-of-ai-driven-crm",
    "vagas-de-tech-lead-agentes-de-ia",
    "vagas-de-gerente-de-agentes-de-ia",
    "vagas-de-lifecycle-marketing-specialist",
    "vagas-de-lifecycle-marketing-manager",
    "vagas-de-retention-marketing-specialist",
    "vagas-de-retention-marketing-manager",
    "vagas-de-especialista-em-engajamento-e-reativacao",
    "vagas-de-especialista-de-prevencao-a-churn",
    "vagas-de-churn-specialist",
    "vagas-de-customer-marketing-specialist",
    "vagas-de-customer-marketing-manager",
    "vagas-de-monetizacao-de-base",
    "vagas-de-marketing-automation-specialist",
    "vagas-de-marketing-automation-architect",
    "vagas-de-especialista-de-martech",
    "vagas-de-analista-de-martech",
    "vagas-de-marketing-operations-analyst",
    "vagas-de-marketing-operations-manager",
    "vagas-de-marketing-ops",
    "vagas-de-arquiteto-de-solucoes-de-marketing",
    "vagas-de-growth-marketing-manager",
    "vagas-de-growth-marketing-specialist",
    "vagas-de-retention-growth-manager",
    "vagas-de-ltv-specialist",
    "vagas-de-ltv-manager",
    "vagas-de-product-growth-analyst",
    "vagas-de-especialista-em-canais-proprietarios",
    "vagas-de-owned-media-specialist",
    "vagas-de-inbound-marketing-specialist",
    "vagas-de-inbound-marketing-manager",
    "vagas-de-messaging-push-notification-specialist",
    "vagas-de-email-marketing-manager",
    "vagas-de-analista-de-mensageria-whatsapp",
    "vagas-de-loyalty-specialist",
    "vagas-de-loyalty-manager",
    "vagas-de-especialista-em-programas-de-fidelidade",
    "vagas-de-gerente-de-programas-de-fidelidade",
    "vagas-de-customer-journey-specialist",
    "vagas-de-customer-journey-manager",
    "vagas-de-especialista-de-mapeamento-de-jornada",
    "vagas-de-customer-experience-specialist",
    "vagas-de-customer-experience-manager",
    "vagas-de-analista-de-voc-voice-of-customer",
    "vagas-de-analista-de-nps",
    "vagas-de-cdp-specialist",
    "vagas-de-customer-data-platform-specialist",
    "vagas-de-customer-data-analyst",
    "vagas-de-customer-intelligence-specialist",
    "vagas-de-database-marketing-analyst",
    "vagas-de-analista-de-segmentacao-consumidor",
    "vagas-de-martech-data-specialist",
    "vagas-de-product-manager-martech",
    "vagas-de-product-manager-lifecycle",
    "vagas-de-product-manager-growth",
    "vagas-de-product-owner-plataformas-de-marketing",
    "vagas-de-analista-de-crm-marketing",
    "vagas-de-analista-de-marketing-de-relacionamento",
    "vagas-de-analista-de-regua-de-relacionamento",
    "vagas-de-analista-de-automacao-de-marketing",
    "vagas-de-analista-de-inbound-marketing",
    "vagas-de-analista-de-lifecycle-marketing",
    "vagas-de-analista-de-retencao-e-engajamento",
    "vagas-de-growth-crm-specialist",
    "vagas-de-retention-specialist",
    "vagas-de-especialista-em-crm-e-ltv",
    "vagas-de-analista-de-crm-data-analytics",
    "vagas-de-analista-de-operacoes-de-crm",
    "vagas-de-crm-ops",
    "vagas-de-especialista-de-growth-e-lifecycle",
    "vagas-de-especialista-de-canais-digitais",
    "vagas-de-digital-channels-specialist",
    "vagas-de-analista-de-programas-de-fidelidade",
    "vagas-de-especialista-em-customer-experience-e-crm",
    "vagas-de-analista-de-omnichannel",
    "vagas-de-coordenador-de-crm-e-growth",
    "vagas-de-coordenador-de-lifecycle-marketing",
    "vagas-de-coordenador-de-marketing-de-relacionamento",
    "vagas-de-gerente-de-crm-e-martech",
    "vagas-de-gerente-de-lifecycle-e-retention",
    "vagas-de-head-de-crm-e-growth",
    "vagas-de-head-de-customer-marketing",
    "vagas-de-head-de-lifecycle-martech",
    "vagas-de-diretor-de-crm-e-customer-experience",
    "vagas-de-crm-lifecycle-marketing-manager",
    "vagas-de-customer-retention-specialist",
    "vagas-de-crm-operations-manager",
    "vagas-de-crm-data-analyst",
    "vagas-de-crm-product-owner",
    "vagas-de-crm",
    "vagas-de-salesforce",
    "vagas-de-hubspot",
    "vagas-de-rd-station",
    "vagas-de-marketing-de-relacionamento",
    "vagas-de-crm-marketing",
    "vagas-de-marketing-automation",
    "vagas-de-braze",
    "vagas-de-klaviyo",
    "vagas-de-pipedrive",
    "vagas-de-dynamics-crm",
    "vagas-de-analista-de-campanhas",
]

def scrape() -> list[dict]:
    vagas = []
    seen = set()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    for slug in SEARCHES:
        try:
            url = f"{BASE_URL}/{slug}"
            resp = session.get(url, timeout=(5, 12))
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("h2.cargo a.link-detalhes-vaga")

            for link in links:
                title = link.get("title", "").strip()
                if not title:
                    title = link.get_text(separator=" ", strip=True)
                if not title:
                    continue

                href = link.get("href", "")
                job_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if not job_url or job_url in seen:
                    continue
                seen.add(job_url)

                category = classify(title)
                if not category:
                    continue

                company_el = soup.select_one(f"#{link.get('id','')} ~ span.emprVaga") if link.get("id") else None
                company = company_el.get_text(strip=True) if company_el else "Não informado"

                vagas.append({
                    "title": title,
                    "company": company,
                    "url": job_url,
                    "location": "Brasil",
                    "description": "",
                    "source": SOURCE,
                    "category": category,
                    "published_at": None,
                })
        except Exception as e:
            print(f"[Vagas.com] Erro '{slug}': {e}")

    print(f"[Vagas.com] {len(vagas)} vagas encontradas")
    return vagas
