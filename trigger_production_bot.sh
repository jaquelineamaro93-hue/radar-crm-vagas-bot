#!/bin/bash
# Script para disparar o bot de vagas em produção (Vercel)
# Executa a varredura completa com paginação V2 (Gupy, Vagas.com, LinkedIn)

set -e

# Configurações
VERCEL_URL="${VERCEL_URL:-https://radar-crm-vagas-bot.vercel.app}"
CRON_SECRET="${CRON_SECRET:-}"

echo "🚀 Disparando bot de vagas em produção..."
echo "URL: $VERCEL_URL"
echo ""

# Opção 1: Chamar endpoint /api/scrape (com CRON_SECRET se necessário)
if [ -z "$CRON_SECRET" ]; then
    echo "⚠️  CRON_SECRET não configurada"
    echo "Tentando sem autenticação..."
    echo ""

    curl -v -X GET "$VERCEL_URL/api/scrape" \
        -H "User-Agent: Bot-Trigger/1.0"
else
    echo "✅ CRON_SECRET encontrada, autenticando..."
    echo ""

    curl -v -X GET "$VERCEL_URL/api/scrape" \
        -H "Authorization: Bearer $CRON_SECRET" \
        -H "User-Agent: Bot-Trigger/1.0"
fi

echo ""
echo "✅ Requisição enviada!"
echo ""
echo "📊 Verificar status:"
echo "   Dashboard: https://conexaocrm.com → Aba 'Vagas de CRM'"
echo "   Logs: https://vercel.com/dashboard (seu projeto)"
echo ""
echo "⏱️  Tempo estimado: 5-10 minutos para coleta completa"
