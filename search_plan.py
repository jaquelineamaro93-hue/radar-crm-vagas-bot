"""Plano único de buscas do Radar, distribuído entre fontes e famílias de cargos.

Cada execução consulta termos genéricos de todas as famílias e uma janela rotativa
da lista integral de títulos cadastrados. Não cria crons por categoria e não remove
títulos previamente solicitados. A classificação final continua feita em classify().
"""
from datetime import datetime, timezone
import os
import re
import unicodedata

DEFAULT_BATCH_SIZE = 16

FAMILIES = [
    ("crm", (r"\bcrm\b", r"relacionamento")),
    ("cxcs", (r"customer success", r"customer experience", r"\bcx\b", r"\bcs\b")),
    ("marketing", (r"marketing", r"martech")),
    ("salesforce", (r"salesforce", r"marketing cloud")),
    ("hubspot", (r"hubspot",)),
    ("growth", (r"growth", r"retention")),
    ("revops", (r"revops", r"revenue operations", r"sales ops")),
    ("data", (r"\bdados\b", r"\bdata\b", r"analytics")),
    ("ia", (r"inteligencia artificial", r"artificial intelligence", r"\bia\b", r"\bai\b")),
    ("product", (r"product design", r"\bux\b", r"\bui\b", r"designer")),
    ("product_owner", (r"product owner", r"product manager")),
    ("quality", (r"\bqa\b", r"quality assurance")),
    ("automation", (r"automacao", r"automation")),
    ("ecommerce", (r"e-commerce", r"ecommerce", r"marketplace")),
]

def _label(term):
    raw = term[0] if isinstance(term,(tuple,list)) else term
    chars = unicodedata.normalize('NFKD',str(raw or '').lower())
    chars = ''.join(c for c in chars if not unicodedata.combining(c))
    return re.sub(r"[_+\-]+"," ",chars)

def select_searches(terms, source='', limit=None, day_index=None):
    """Não prioriza fonte ou uma única categoria; mantém cobertura rotativa."""
    terms=list(dict.fromkeys(terms or ()))
    if not terms:return []
    limit=max(1,min(40,int(limit or os.getenv('RADAR_QUERIES_PER_SOURCE',DEFAULT_BATCH_SIZE))))
    if len(terms)<=limit:return terms
    labels=[_label(t) for t in terms]
    selected=[]
    used=set()
    for _,patterns in FAMILIES:
        candidates=[i for i,t in enumerate(labels) if i not in used and any(re.search(p,t) for p in patterns)]
        if not candidates:continue
        choice=min(candidates,key=lambda i:(len(labels[i]),i))
        used.add(choice);selected.append(choice)
        if len(selected)>=limit:return [terms[i] for i in selected]
    remaining=[i for i in range(len(terms)) if i not in used]
    if day_index is None:
        day_index=datetime.now(timezone.utc).date().toordinal()
    window=limit-len(selected)
    start=(day_index*max(1,window))%len(remaining)
    selected.extend(remaining[(start+j)%len(remaining)] for j in range(window))
    return [terms[i] for i in selected]
