# 🚀 Como Disparar o Bot em Produção (Vercel)

**Data:** 2026-09-09  
**Objetivo:** Forçar execução imediata do bot com paginação V2 expandida

---

## 📍 Localização do Bot

- **Ambiente:** Vercel (Produção)
- **URL Base:** https://radar-crm-vagas-bot.vercel.app
- **Endpoint:** `/api/scrape`
- **Método:** GET
- **Segurança:** CRON_SECRET (Bearer token)

---

## 🎯 O Que Vai Acontecer

Quando disparado, o bot vai:

1. **Gupy** (34 queries)
   - ✅ Loop até 10 páginas × 20 vagas = até 200/query
   - Impacto: ~6.800 vagas

2. **Vagas.com** (23 queries)
   - ✅ Loop até 15 páginas × 40 vagas = até 600/query
   - Impacto: ~13.800 vagas

3. **LinkedIn** (75 keywords)
   - ✅ Loop até 10 páginas × 25 vagas = até 250/keyword
   - Impacto: ~18.750 vagas

4. **Catho, 99jobs, InfoJobs, Solides** (adicionais)
   - Cada um também com paginação expandida
   - Impacto: +1.000-2.000 vagas

5. **Deduplikação Global**
   - Remove duplicatas via `url_hash`
   - Resultado esperado: **~10.000 vagas únicas**

6. **Limpeza de Vagas Fechadas**
   - Remove URLs com 404/403/410
   - Mantém apenas vagas ativas

---

## 🔑 Opção 1: Com CRON_SECRET (Seguro)

### Passo 1: Configurar Variável de Ambiente

```bash
export CRON_SECRET="seu_secret_aqui"
export VERCEL_URL="https://radar-crm-vagas-bot.vercel.app"
```

Para encontrar o CRON_SECRET:
- Ir em: https://vercel.com/dashboard
- Projeto: `radar-crm-vagas-bot`
- Settings → Environment Variables
- Procurar por `CRON_SECRET`

### Passo 2: Executar

```bash
chmod +x trigger_production_bot.sh
./trigger_production_bot.sh
```

Ou manualmente:

```bash
curl -X GET "https://radar-crm-vagas-bot.vercel.app/api/scrape" \
  -H "Authorization: Bearer seu_secret_aqui" \
  -H "User-Agent: Bot-Trigger/1.0"
```

---

## 🔓 Opção 2: Sem CRON_SECRET (Se Não Configurado)

Se a app foi deployada sem CRON_SECRET, pode chamar diretamente:

```bash
curl -X GET "https://radar-crm-vagas-bot.vercel.app/api/scrape" \
  -H "User-Agent: Bot-Trigger/1.0"
```

**Resposta esperada:**
```json
{
  "status": "ok",
  "novas_vagas": 10000,
  "vagas_removidas": 50
}
```

---

## 🔍 Opção 3: Debug - Testar Scraping sem BD

Para ver quantas vagas cada fonte consegue raspar (sem escrever no BD):

```bash
curl -X GET "https://radar-crm-vagas-bot.vercel.app/api/debug" \
  -H "User-Agent: Bot-Trigger/1.0"
```

Resposta inclui:
```json
{
  "total_vagas": 9500,
  "sources": {
    "gupy": {"status": "ok", "count": 2150, "elapsed_s": 45.2},
    "vagascom": {"status": "ok", "count": 3200, "elapsed_s": 38.1},
    "linkedin": {"status": "ok", "count": 2800, "elapsed_s": 52.3},
    "catho": {"status": "ok", "count": 800, "elapsed_s": 15.2},
    ...
  }
}
```

---

## ⏱️ Tempo de Execução

Estimado:

| Fase | Tempo |
|------|-------|
| Gupy (34 × 10 páginas) | ~45s |
| Vagas.com (23 × 15 páginas) | ~40s |
| LinkedIn (75 × 10 páginas) | ~60s |
| Catho, 99jobs, InfoJobs | ~30s |
| Deduplikação + BD | ~15s |
| Limpeza vagas fechadas | ~10s |
| **TOTAL** | **~200s (3-4 min)** |

---

## ✅ Validar Resultado

### 1. Contar Vagas no BD

```bash
curl -X GET "https://rwkbpafpniwzvlkfngag.supabase.co/rest/v1/vagas_crm?select=count()" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY"

# Resposta esperada: count >= 10000
```

### 2. Ver Últimas Vagas Inseridas

```bash
curl -X GET "https://rwkbpafpniwzvlkfngag.supabase.co/rest/v1/vagas_crm?select=title,company,source,found_at&order=found_at.desc&limit=10" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY"
```

### 3. Dashboard

Acesse: https://conexaocrm.com → Aba "Vagas de CRM"

Deve mostrar 10.000+ vagas com profundo de dados em tempo real!

---

## 🐛 Troubleshooting

### Erro: "Unauthorized" (401)

```
❌ {"error": "Unauthorized"}
```

**Solução:** CRON_SECRET está errado

```bash
# Verificar secret
echo $CRON_SECRET

# Se vazio, obter de Vercel
# https://vercel.com/dashboard → radar-crm-vagas-bot → Settings → Environment Variables
```

### Erro: "Timeout" (504)

```
❌ {"status": "error", "message": "timeout"}
```

**Solução:** Bot levou mais de 30s (limite Vercel para serverless)

- Aumentar timeout em `app.py` (se possível)
- Ou reduzir `max_pages` em scrapers (mas isso reduz volume)

### Erro: "Service Unavailable" (503)

```
❌ {"status": "error", "message": "Service Unavailable"}
```

**Solução:** Vercel temporariamente offline ou rate limit da fonte

- Tentar novamente em 1 minuto
- Verificar status: https://status.vercel.com

### Vagas Não Aparecem no Dashboard

```
✗ Dashboard ainda mostra 20 vagas
```

**Solução:**

1. Verificar se scraping foi sucesso:
   ```bash
   curl -X GET "https://radar-crm-vagas-bot.vercel.app/api/debug"
   ```
   
2. Verificar Supabase:
   ```bash
   SELECT COUNT(*) FROM vagas_crm;
   ```

3. Verificar query do dashboard (index.html:5956):
   ```javascript
   // Deve estar usando índice:
   SELECT id, title, company, location, url, found_at, source, cargo
   FROM vagas_crm ORDER BY found_at DESC LIMIT 300
   ```

4. Limpar cache do browser:
   - Ctrl+Shift+Delete (ou Cmd+Shift+Delete no Mac)
   - Hard refresh: Ctrl+F5

---

## 📋 Checklist Pré-Disparo

- [ ] CRON_SECRET obtido de Vercel Settings
- [ ] VERCEL_URL confirmada (prod ou staging)
- [ ] Internet conectada
- [ ] curl ou similar instalado
- [ ] Supabase keys acessíveis
- [ ] Dashboard aberto para validar resultado

---

## 🎬 Passo-a-Passo Completo

### Local (Este Ambiente)

```bash
# 1. Ir para bot
cd /home/user/radar-crm-vagas-bot

# 2. Exportar variáveis
export CRON_SECRET="..." # de Vercel Settings
export VERCEL_URL="https://radar-crm-vagas-bot.vercel.app"

# 3. Disparar
curl -X GET "$VERCEL_URL/api/scrape" \
  -H "Authorization: Bearer $CRON_SECRET" \
  -v
```

### Terminal Direto

```bash
chmod +x /home/user/radar-crm-vagas-bot/trigger_production_bot.sh
/home/user/radar-crm-vagas-bot/trigger_production_bot.sh
```

### GitHub Actions (Se Configurado)

Se há Actions configuradas em `.github/workflows/`:

```bash
gh workflow run scrape.yml
```

---

## 📊 Resultado Esperado

**Após 3-4 minutos:**

```
Dashboard mostra:
✅ 10.000+ vagas
✅ Últimas vagas: hoje
✅ Fontes: 7 (Gupy, Vagas.com, LinkedIn, Catho, 99jobs, InfoJobs, Solides)
✅ Response time: < 100ms
✅ Match: Profissional ↔ Vaga funcionando
```

---

## 🔄 Scheduler Automático (Já Configurado)

Bot também roda automaticamente:

```
Horário: 09:00 UTC (diariamente)
Endpoint: /api/scrape
Configurado em: vercel.json → crons
```

Você pode desabilitar ou mudar em: Vercel Dashboard → Project Settings → Cron Jobs

---

## 📞 Suporte

Se não conseguir disparar:

1. **Verificar CRON_SECRET:**
   - https://vercel.com/dashboard
   - Projeto → Settings → Environment Variables

2. **Verificar logs:**
   - https://vercel.com/dashboard
   - Projeto → Deployments → Logs

3. **Testar endpoint:**
   ```bash
   curl -I https://radar-crm-vagas-bot.vercel.app/api/scrape
   # Deve retornar 400/401/200, não 404
   ```

4. **Validar Supabase connection:**
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_ANON_KEY
   # Ambos devem estar em Vercel Environment Variables
   ```

---

**Status:** ✅ Pronto para Disparar  
**Ação:** Execute um dos comandos acima para ativar o bot em produção

_Gerado em 2026-09-09 via Claude Code_
