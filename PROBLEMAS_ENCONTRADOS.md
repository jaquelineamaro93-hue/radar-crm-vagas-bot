# 🔍 Problemas Encontrados - Bot de Vagas

**Data:** 2026-09-09  
**Status:** Parcialmente Corrigido

---

## 🚨 Problema 1: Duplicação Tripla de Vagas

### Local
**Arquivo:** `main.py` - Linhas 74-78

### O Que Estava Acontecendo
```python
# ❌ ERRADO - Antes (código bugado)
upload_to_supabase(vaga)
upload_to_supabase(vaga)  # DUPLICADA!
upload_to_supabase(vaga)  # DUPLICADA!
```

Cada vaga estava sendo inserida **3 VEZES** na tabela `vagas_scraper`!

### ✅ Corrigido
```python
# ✅ CORRETO - Agora
upload_to_supabase(vaga)  # Uma única vez
sync_vaga_crm(vaga)        # Sincroniza para vagas_crm (se categoria=crm)
```

### Impacto
- **Antes:** 169 vagas únicas × 3 = 507 registros (mínimo esperado)
- **Realidade:** 5.956.107 registros (devido às 5.9M duplicatas já presentes)

---

## 🔴 Problema 2: Vagas_CRM Sobrecarregada com 5.9M Duplicatas

### Causa
- Bot estava rodando enquanto a tabela tinha 5.9M registros
- Queries dão TIMEOUT ao tentar processar tabela tão grande

### Resultado
```
❌ Dashboard mostra: "0 vagas"
❌ Erro: "cancelling statement due to statement timeout"
```

### ✅ Solução em Andamento
1. Limpar as 5.9M duplicatas (você já fez isso? 🤔)
2. Executar bot novamente para trazer vagas

---

## ❓ Problema 3: Registros Voltando para Google Sheets (INVESTIGAR)

### O Que Está Acontecendo
- Google Sheets "Open to Work" recebeu 5.9M vagas (ERRADO!)
- Ela deveria ter apenas ~300 profissionais (dados de Forms)

### O Bot NÃO Está Escrevendo Lá
```python
# ✅ Bot apenas LÊ Google Sheets (correto)
_fetch_otw_candidates()  # Lê via CSV publicado
# ❌ Bot NÃO escreve em Google Sheets
```

### Possíveis Culpados
1. **Webhook Supabase** → Pode estar copiando dados de `vagas_crm` para Google Sheets
2. **Automação Zapier/Make** → Pode estar sincronizando tabelas
3. **Outro Bot** → Existe algum outro script que escreve em Google Sheets?
4. **Google Apps Script** → Há algum script automático na Google Sheets?

### ✅ Ação Necessária
**Verifique no Supabase:**
1. Vá em **Database → Webhooks**
2. Procure por webhooks que tocam em `vagas_crm` ou `vagas_scraper`
3. Verifique se algum webhook está enviando dados para Google Sheets
4. **Desative ou remova** se encontrar

**Verifique na Google Sheets:**
1. Abra a Google Sheets
2. Menu **Tools → Script Editor**
3. Procure por scripts que fazem `append_row()` ou `insert()`
4. **Remova ou desative** se encontrar

**Verifique Automações Externas:**
- Zapier, Make, IFTTT
- Procure por "vagas" ou "Radar CRM"
- Desative qualquer automação que escreva em Google Sheets

---

## 📋 Próximos Passos - ORDEM EXATA

### ✅ Já Feito
- [x] Remover duplicação tripla em main.py

### 🔄 Em Andamento
- [ ] **VOCÊ:** Limpar 5.9M duplicatas (use `LIMPEZA_DUPLICATAS_MANUAL.md`)
- [ ] **VOCÊ:** Verificar Supabase Webhooks
- [ ] **VOCÊ:** Verificar Google Sheets Scripts
- [ ] **VOCÊ:** Verificar Automações Externas (Zapier, Make)

### ⏳ Depois de Limpar
- [ ] Executar bot novamente (GET /api/scrape)
- [ ] Verificar se vagas aparecem no dashboard
- [ ] Confirmar que Google Sheets não recebe dados

---

## 🧹 Como Limpar as 5.9M Duplicatas

**Se ainda não fez:**
1. Abra: https://app.supabase.co
2. Vá em **SQL Editor**
3. Execute (vários vezes):
```sql
DELETE FROM vagas_crm
WHERE id NOT IN (
  SELECT DISTINCT ON (cargo, empresa) id 
  FROM vagas_crm 
  ORDER BY cargo, empresa
)
LIMIT 10000;
```

Execute ~600 vezes até `COUNT(*) ≈ 169`

**Depois:**
```sql
ALTER TABLE vagas_crm 
ADD CONSTRAINT unique_cargo_empresa UNIQUE (cargo, empresa);
```

---

## 📊 Status Geral

| Item | Status | Ação |
|------|--------|------|
| Duplicação tripla em main.py | ✅ CORRIGIDO | Commit & push |
| 5.9M duplicatas em vagas_crm | 🔄 LIMPANDO | Você faz |
| Registros em Google Sheets | ❓ INVESTIGANDO | Você verifica |
| Vagas aparecem no dashboard | ⏳ AGUARDANDO | Depois de limpar |

---

**Arquivo:** `main.py`  
**Branch:** `claude/rls-security-audit-bwg48a` (dashboard) + seu branch (bot)  
**Próximo passo:** Você limpa as 5.9M e me avisa! 🚀
