import re

TERMOS_COPY_DESIGN = [
    # Copywriting / Conteúdo / Mensageria
    "crm copywriter",
    "lifecycle copywriter",
    "redator de ciclo de vida",
    "growth copywriter",
    "growth writer",
    "copywriter de inbound e automacao",
    "copywriter de mensageria e conversao",
    "copywriter whatsapp push sms",
    "copywriter de revops",
    "copywriter sales enablement",
    "conversational copywriter",
    "redator para agentes de ia e bots",
    "email marketing copywriter",
    "ux writer microcopy",
    "ux writer jornadas",
    "ux writer reguas",
    # Design / Visual / Email
    "crm designer",
    "lifecycle designer",
    "designer de relacionamento",
    "growth designer",
    "designer de automacao de marketing",
    "email marketing designer",
    "designer html css email",
    "designer de canais proprietarios",
    "designer owned media",
    "designer whatsapp push in-app",
    "visual designer retencao",
    "visual designer ltv",
    "martech visual specialist",
    "designer braze insider",
    "ui designer jornadas de clientes",
    "designer de ciclo de vida",
    "designer de growth e retencao",
    "designer para plataformas de automacao",
    "designer rd station braze insider",
    "designer programas de fidelidade",
    # Híbridos / Estratégicos
    "creative growth specialist",
    "especialista de criacao para growth",
    "conversational experience designer",
    "especialista de conteudo hubspot rd station",
    "braze content specialist",
    "insider content specialist",
    "revops creative specialist",
    "creative operations specialist martech",
    "especialista em criacao e design regua de relacionamento",
    "especialista em operacoes criativas martech",
    # Redação CRM
    "redator de crm",
    "redator de crm marketing",
    "redator lifecycle",
    "copywriter de retencao e nutricao",
    "copywriter inbound rd station hubspot",
    "redator de mensageria whatsapp sms push",
    "redator revops cadencias de vendas",
    "redator de email marketing",
    "redator regua de relacionamento",
    # IA Conversacional + Fluxos
    "redator conversacional bots",
    "designer de experiencia conversacional",
    "especialista em conteudo e prompting ia crm",
    "arquiteto de fluxos conversacionais",
    "designer fluxos whatsapp kommo",
    # Marketing Cloud / Salesforce extra
    "salesforce marketing cloud specialist",
    "salesforce marketing cloud developer",
    "salesforce marketing cloud architect",
    "marketing cloud consultant",
    "marketing cloud email specialist",
]

def patch_file(path, old_marker, fmt_fn):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    novas = "\n".join(fmt_fn(t) for t in TERMOS_COPY_DESIGN)
    content = content.replace(old_marker, old_marker + "\n" + novas, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK {path} — {len(TERMOS_COPY_DESIGN)} termos")

patch_file("scrapers/linkedin.py",  'SEARCHES = [', lambda t: f'    ("{t}", "Brazil", "2", "r5184000"),')
patch_file("scrapers/gupy.py",      'searches = [', lambda t: f'        "{t}",')
patch_file("scrapers/catho.py",     'SEARCHES = [', lambda t: f'    "{t.replace(" ","-")}",')
patch_file("scrapers/infojobs.py",  'SEARCHES = [', lambda t: f'    ("vagas-de-emprego-{t.replace(" ","-")}-trabalho-home-office", True, None),')
patch_file("scrapers/vagascom.py",  'SEARCHES = [', lambda t: f'    "vagas-de-{t.replace(" ","-")}",')

# config.py
with open("config.py", "r", encoding="utf-8") as f:
    cfg = f.read()
novas_cfg = "\n".join(f'        "{t}",' for t in TERMOS_COPY_DESIGN)
cfg = re.sub(r'("crm": \[)', r'\1\n        # Copy + Design + Conversacional\n' + novas_cfg + '\n', cfg, count=1)
with open("config.py", "w", encoding="utf-8") as f:
    f.write(cfg)
print(f"OK config.py")
print(f"\nPRONTO! {len(TERMOS_COPY_DESIGN)} termos adicionados.")
