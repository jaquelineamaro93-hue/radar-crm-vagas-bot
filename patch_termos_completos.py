import re

NOVOS_TERMOS = [
    "forward deployed engineer","fde ai martech","ai agent architect",
    "ai agent product manager","ai solutions architect crm",
    "desenvolvedor de agentes de ia","engenheiro de integracao de agentes",
    "especialista em crm e inteligencia artificial","ai lifecycle marketing",
    "crm preditivo","predictive crm specialist","ai-driven growth specialist",
    "analista de dados de crm machine learning","real-time personalization specialist",
    "ia conversacional","conversational ai specialist","prompt engineer crm",
    "prompt engineer cx","conversational ai product owner",
    "automacao de atendimento ia generativa","arquiteto de bots agentes autonomos",
    "ai martech operations specialist","cdp ai data specialist",
    "orquestracao de agentes crm","engenheiro de dados de consumidor ia",
    "head of ai customer experience","head of ai-driven crm",
    "tech lead agentes de ia","gerente de agentes de ia",
    "lifecycle marketing specialist","lifecycle marketing manager",
    "retention marketing specialist","retention marketing manager",
    "especialista em engajamento e reativacao","especialista de prevencao a churn",
    "churn specialist","customer marketing specialist","customer marketing manager",
    "monetizacao de base","marketing automation specialist","marketing automation architect",
    "especialista de martech","analista de martech","marketing operations analyst",
    "marketing operations manager","marketing ops","arquiteto de solucoes de marketing",
    "growth marketing manager","growth marketing specialist","retention growth manager",
    "ltv specialist","ltv manager","product growth analyst",
    "especialista em canais proprietarios","owned media specialist",
    "inbound marketing specialist","inbound marketing manager",
    "messaging push notification specialist","email marketing manager",
    "analista de mensageria whatsapp","loyalty specialist","loyalty manager",
    "especialista em programas de fidelidade","gerente de programas de fidelidade",
    "customer journey specialist","customer journey manager",
    "especialista de mapeamento de jornada","customer experience specialist",
    "customer experience manager","analista de voc voice of customer","analista de nps",
    "cdp specialist","customer data platform specialist","customer data analyst",
    "customer intelligence specialist","database marketing analyst",
    "analista de segmentacao consumidor","martech data specialist",
    "product manager martech","product manager lifecycle","product manager growth",
    "product owner plataformas de marketing","analista de crm marketing",
    "analista de marketing de relacionamento","analista de regua de relacionamento",
    "analista de automacao de marketing","analista de inbound marketing",
    "analista de lifecycle marketing","analista de retencao e engajamento",
    "growth crm specialist","retention specialist","especialista em crm e ltv",
    "analista de crm data analytics","analista de operacoes de crm","crm ops",
    "especialista de growth e lifecycle","especialista de canais digitais",
    "digital channels specialist","analista de programas de fidelidade",
    "especialista em customer experience e crm","analista de omnichannel",
    "coordenador de crm e growth","coordenador de lifecycle marketing",
    "coordenador de marketing de relacionamento","gerente de crm e martech",
    "gerente de lifecycle e retention","head de crm e growth",
    "head de customer marketing","head de lifecycle martech",
    "diretor de crm e customer experience","crm lifecycle marketing manager",
    "customer retention specialist","crm operations manager","crm data analyst",
    "crm product owner",
]

def patch_file(path, old_marker, fmt_fn):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    novas = "\n".join(fmt_fn(t) for t in NOVOS_TERMOS)
    content = content.replace(old_marker, old_marker + "\n" + novas, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK {path}")

patch_file("scrapers/linkedin.py",  'SEARCHES = [', lambda t: f'    ("{t}", "Brazil", "2", "r5184000"),')
patch_file("scrapers/gupy.py",      'searches = [', lambda t: f'        "{t}",')
patch_file("scrapers/catho.py",     'SEARCHES = [', lambda t: f'    "{t.replace(" ","-")}",')
patch_file("scrapers/infojobs.py",  'SEARCHES = [', lambda t: f'    ("vagas-de-emprego-{t.replace(" ","-")}-trabalho-home-office", True, None),')
patch_file("scrapers/vagascom.py",  'SEARCHES = [', lambda t: f'    "vagas-de-{t.replace(" ","-")}",')

# config.py — adicionar no bloco crm
with open("config.py", "r", encoding="utf-8") as f:
    cfg = f.read()
novas_cfg = "\n".join(f'        "{t}",' for t in NOVOS_TERMOS)
cfg = re.sub(r'("crm": \[)', r'\1\n        # IA + Lifecycle + CX + MarTech\n' + novas_cfg + '\n', cfg, count=1)
with open("config.py", "w", encoding="utf-8") as f:
    f.write(cfg)
print("OK config.py")
print(f"\nPRONTO! {len(NOVOS_TERMOS)} termos adicionados.")
