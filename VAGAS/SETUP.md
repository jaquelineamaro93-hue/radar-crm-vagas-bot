# Bot de Vagas — CX/CS & Design → Discord

Scraper que coleta vagas de múltiplas fontes, deduplica e envia para canais do Discord.

## Fontes cobertas

| Fonte          | Tipo                | Status   |
|----------------|---------------------|----------|
| VagasRemotas   | BS4 scrape          | ✅       |
| LinkedIn       | API pública (guest) | ✅       |
| Indeed BR      | BS4 scrape          | ✅       |
| Behance        | BS4 scrape          | ✅       |
| Dribbble       | BS4 scrape          | ✅       |
| InHire         | BS4 scrape          | ✅       |
| Gupy           | API pública         | ✅       |
| Remotar        | BS4 scrape          | ✅       |

## Pré-requisitos

- Python 3.11+
- Servidor ou PC que fique ligado (ou rode no Railway/Render)

---

## 1. Instalação local

```bash
# Clone ou copie a pasta VAGAS para algum lugar
cd VAGAS

# Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt
```

---

## 2. Configurar Discord Webhooks

### Criar um Webhook no Discord

1. Abra o Discord → canal desejado → **Configurações do canal** (engrenagem)
2. **Integrações** → **Webhooks** → **Novo Webhook**
3. Dê um nome (ex: `Bot Vagas Designer`)
4. Copie a **URL do Webhook**

Recomendado: crie **2 canais** e **2 webhooks** separados:
- `#vagas-design` → para Designer/UX/UI
- `#vagas-cxcs` → para Customer Success/Experience

### Configurar o `.env`

```bash
cp .env.example .env
```

Edite o `.env` e cole as URLs:

```env
DISCORD_WEBHOOK_DESIGNER=https://discord.com/api/webhooks/123456789/abcdef...
DISCORD_WEBHOOK_CXCS=https://discord.com/api/webhooks/987654321/xyz...
```

---

## 3. Rodar

### Execução única (teste)

```bash
python main.py
```

### Modo contínuo (roda a cada 6h)

```bash
python scheduler.py
```

---

## 4. Implantar no Railway (gratuito / $5/mês)

Railway mantém o processo rodando 24/7.

```bash
# Instale o CLI
npm install -g @railway/cli

# Login
railway login

# Crie projeto
railway init

# Adicione variáveis de ambiente
railway variables set DISCORD_WEBHOOK_DESIGNER=https://...
railway variables set DISCORD_WEBHOOK_CXCS=https://...

# Deploy
railway up
```

No `Procfile` (já criado automaticamente pelo Railway detectando Python), defina:
```
worker: python scheduler.py
```

---

## 5. Implantar no Render (gratuito)

1. Crie conta em [render.com](https://render.com)
2. **New → Background Worker**
3. Aponte para o repositório Git
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `python scheduler.py`
6. Em **Environment Variables**, adicione `DISCORD_WEBHOOK_DESIGNER` e `DISCORD_WEBHOOK_CXCS`

---

## 6. Implantar via Cron local (Windows Task Scheduler)

Se preferir rodar no próprio PC:

1. Abra **Agendador de Tarefas** → **Criar Tarefa Básica**
2. Nome: `Bot Vagas`
3. Gatilho: **Diariamente**, repetir a cada 6 horas
4. Ação: `python.exe` com argumento `C:\caminho\para\VAGAS\main.py`
5. Marque **Executar mesmo que o usuário não esteja conectado**

---

## 7. Estrutura do projeto

```
VAGAS/
├── main.py            — Ponto de entrada, orquestra tudo
├── scheduler.py       — Loop contínuo (roda a cada 6h)
├── config.py          — Keywords e configurações
├── database.py        — SQLite para deduplicação
├── notifier.py        — Envia embed para Discord
├── scrapers/
│   ├── base.py        — fetch() + classify() compartilhados
│   ├── vagasremotas.py
│   ├── linkedin.py
│   ├── indeed.py
│   ├── behance.py
│   ├── dribbble.py
│   ├── inhire.py
│   ├── gupy.py
│   └── remotar.py
├── requirements.txt
├── .env.example
└── vagas.db           — Criado automaticamente na 1ª execução
```

---

## 8. Como funciona a deduplicação

Cada vaga é identificada por um hash SHA-256 de:
```
titulo_normalizado | empresa_normalizada | url
```

Na primeira execução, todas as vagas encontradas são salvas no banco e enviadas ao Discord. Nas execuções seguintes, só vagas com hash novo (inéditas) são enviadas.

---

## 9. Adicionar novas palavras-chave

Edite `config.py`, seção `KEYWORDS`:

```python
KEYWORDS = {
    "designer": [
        "motion designer",   # ← adicione aqui
        ...
    ],
    "cxcs": [
        "retention",         # ← ou aqui
        ...
    ],
}
```

---

## Observações

- **LinkedIn e Indeed** têm proteção anti-bot. Se bloquearem, o scraper ignora e segue.  
  Para mais robustez, considere proxies rotativos ou a API oficial do LinkedIn (requer aplicação).
- **Gupy** usa API pública JSON — é a fonte mais confiável do Brasil.
- O delay entre requests (`REQUEST_DELAY = 2s`) é intencional para não ser bloqueado.
