"""Importação incremental de respostas do Open to Work: CSV público -> Supabase.

Conserva os IDs. Mantém dados brutos em staging privado. Só insere/atualiza
perfis públicos com aceite explícito de divulgação no CSV. Falha da planilha
nunca apaga profissionais já cadastrados.
"""
import csv
import hashlib
import io
import os
import re
import unicodedata
import requests
from datetime import datetime, timezone

SHEET_GID="1463680290"
SHEET_URL=("https://docs.google.com/spreadsheets/d/e/"
 "2PACX-1vRtuTLaOZzk-uRDdRchwdNmypGJ8eO2K7qdckkL7Sh0VohIa8OHWMDbKuDDHQMsoLYOhMfIMlplKoop/"
 "pub?gid="+SHEET_GID+"&single=true&output=csv")


def _norm(s):
    text=unicodedata.normalize("NFKD",str(s or "").strip().lower())
    text="".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\\s+"," ",text)

def _field(row,*needles):
    for needle in needles:
        for key,value in row.items():
            if needle in _norm(key) and str(value or "").strip():
                return str(value).strip()
    return ""

def _consent(row):
    for key,value in row.items():
        label=_norm(key)
        if any(term in label for term in ("lgpd","autorizo divulg","autoriza divulg","consentimento","aceito divulg","publicar perfil","perfil publico","tornar visivel")):
            accepted=_norm(value)
            if accepted in ("sim","aceito","autorizo","concordo","true","yes","1") or accepted.startswith(("sim,","sim ","li e aceito","aceito os termos","concordo com")):
                return True
    return False

def _source_key(row):
    email=_norm(_field(row,"e-mail","email")).strip()
    linkedin=_norm(_field(row,"linkedin"))
    whatsapp=re.sub(r"\\D","","".join([_field(row,"whatsapp","telefone")]))
    nome=_norm(_field(row,"nome"))
    identity=("email:"+email if email else "linkedin:"+linkedin if linkedin else "whatsapp:"+whatsapp+":"+nome if whatsapp and nome else "")
    return hashlib.sha256(identity.encode()).hexdigest() if identity else None

def _sb_request(method,table,service,base,**kwargs):
    headers={"apikey":service,"Authorization":"Bearer "+service,
             "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=representation"}
    response=requests.request(method,base+"/rest/v1/"+table,headers=headers,timeout=16,**kwargs)
    if not response.ok:
        raise RuntimeError("Supabase "+table+" HTTP "+str(response.status_code)+" "+response.text[:170])
    if response.content:
        return response.json()
    return []

def _public_payload(row, key):
    return {
        "sheet_source_key":key,
        "sheet_sync_source":"published_csv:"+SHEET_GID,
        "sheet_last_seen_at":datetime.now(timezone.utc).isoformat(),
        "nome":_field(row,"nome completo","nome"),
        "email":_field(row,"e-mail","email") or None,
        "senioridade":_field(row,"senioridade"),
        "area_atuacao":_field(row,"area de atuacao","área de atuação"),
        "tempo_experiencia":_field(row,"tempo de experiencia","tempo de experiência"),
        "ferramentas":_field(row,"ferramentas"),
        "localizacao":_field(row,"localizacao","localização","cidade"),
        "condicao_trabalho":_field(row,"condicao de trabalho","condição de trabalho","modalidade"),
        "mudar_cidade":_field(row,"mudanca","mudança","mudar de cidade"),
        "linkedin":_field(row,"linkedin"),
        "whatsapp":re.sub(r"\\D","",_field(row,"whatsapp","telefone")) or None,
        "ultima_empresa":_field(row,"ultima empresa","última empresa"),
        "idioma":_field(row,"idioma","ingles","inglês"),
    }

def sync_sheet():
    base=os.environ.get("SUPABASE_URL","").rstrip("/")
    service=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
    if not base or not service:raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY ausente")
    report={"gid":SHEET_GID,"received":0,"staged":0,"published":0,"skipped_no_consent":0,"skipped_user_owned":0,"errors":0}
    runs=_sb_request("POST","crm_otw_sheet_sync_runs",service,base,json={"status":"running"})
    run_id=runs[0]["id"] if runs else None
    try:
        response=requests.get(SHEET_URL,timeout=(5,22),headers={"User-Agent":"ConexaoCRM/1.0"})
        response.raise_for_status()
        if len(response.content)>3_000_000:raise ValueError("CSV excedeu limite de segurança")
        decoded=response.content.decode("utf-8-sig")
        rows=list(csv.DictReader(io.StringIO(decoded)))
        if not rows or len(rows)>5000:raise ValueError("CSV vazio ou acima do limite")
        if not any("nome" in _norm(h) for h in rows[0].keys()):
            raise ValueError("Cabeçalho Nome não encontrado; não importar estrutura inesperada")
        report["received"]=len(rows)
        staged=[]
        for i,row in enumerate(rows,start=2):
            if not isinstance(row,dict):continue
            source_key=_source_key(row)
            if not source_key:continue
            staged.append({"source_key":source_key,"sheet_gid":SHEET_GID,"row_number":i,
                           "payload":{str(k):str(v or "")[:3500] for k,v in row.items() if k is not None},
                           "last_seen_at":datetime.now(timezone.utc).isoformat()})
        for offset in range(0,len(staged),100):
            part=staged[offset:offset+100]
            if not part:continue
            _sb_request("POST","crm_otw_sheet_import",service,base,
                        params={"on_conflict":"source_key"},json=part)
            report["staged"]+=len(part)
        for row in rows:
            key=_source_key(row)
            if not key:continue
            if not _consent(row):
                report["skipped_no_consent"]+=1
                continue
            payload=_public_payload(row,key)
            if not payload["nome"]:continue
            email=payload["email"]
            try:
                lookup={"select":"id,created_by,sheet_source_key","limit":"1"}
                if email:lookup["email"]="eq."+email
                else:lookup["sheet_source_key"]="eq."+key
                current=_sb_request("GET","profissionais_open_to_work",service,base,params=lookup)
                if current:
                    if current[0].get("created_by"):
                        report["skipped_user_owned"]+=1
                        continue
                    _sb_request("PATCH","profissionais_open_to_work",service,base,
                                params={"id":"eq."+str(current[0]["id"])},json=payload)
                else:
                    _sb_request("POST","profissionais_open_to_work",service,base,json=payload)
                report["published"]+=1
            except Exception as err:
                report["errors"]+=1
                print("[OTW] Registro não publicado:",type(err).__name__)
        if run_id:
            _sb_request("PATCH","crm_otw_sheet_sync_runs",service,base,
                params={"id":"eq."+run_id},json={
                    "status":"success" if not report["errors"] else "partial",
                    "finished_at":datetime.now(timezone.utc).isoformat(),
                    "rows_received":report["received"],"rows_staged":report["staged"],
                    "rows_published":report["published"],
                    "error_summary":(str(report["errors"])+" linhas exigem revisão") if report["errors"] else None})
        return report
    except Exception as exc:
        if run_id:
            try:
                _sb_request("PATCH","crm_otw_sheet_sync_runs",service,base,
                    params={"id":"eq."+run_id},json={"status":"error",
                        "finished_at":datetime.now(timezone.utc).isoformat(),
                        "error_summary":type(exc).__name__+": "+str(exc)[:240]})
            except Exception:pass
        raise
