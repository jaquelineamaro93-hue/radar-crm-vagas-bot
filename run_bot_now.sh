#!/bin/bash
# Dispara o bot de vagas AGORA em produção
# Monitora os logs do Vercel em tempo real

set -e

VERCEL_URL="https://radar-crm-vagas-bot.vercel.app"

echo "🚀 DISPARANDO BOT DE VAGAS EM PRODUÇÃO"
echo "=========================================="
echo "URL: $VERCEL_URL"
echo "Disparando: $(date)"
echo ""

if [ -z "$CRON_SECRET" ]; then
    echo "⚠️  AVISO: CRON_SECRET não definida"
    echo "Tentando disparar sem autenticação..."
    echo ""
    curl -s -X GET "$VERCEL_URL/api/scrape" \
        -H "User-Agent: Bot-Trigger/1.0" | jq .
else
    echo "✅ Usando CRON_SECRET para autenticar"
    echo ""
    curl -s -X GET "$VERCEL_URL/api/scrape" \
        -H "Authorization: Bearer $CRON_SECRET" \
        -H "User-Agent: Bot-Trigger/1.0" | jq .
fi

echo ""
echo "=========================================="
echo "✅ BOT DISPARADO!"
echo ""
echo "📊 PRÓXIMAS AÇÕES:"
echo "   1. Acompanhar logs:"
echo "      https://vercel.com/dashboard"
echo ""
echo "   2. Verificar vagas inseridas:"
echo "      https://conexaocrm.com → Aba 'Vagas de CRM'"
echo ""
echo "   3. Aguardar 3-5 minutos para conclusão da coleta"
echo ""
echo "⏱️  Tempo estimado: 3-5 minutos"
