
alter table public.vagas_scraper
  add column if not exists trilha text,
  add column if not exists subcategoria text,
  add column if not exists area_correlata boolean;

alter table public.vagas_crm
  add column if not exists trilha text,
  add column if not exists subcategoria text,
  add column if not exists area_correlata boolean;

create or replace function public.classificar_taxonomia_vaga()
returns trigger
language plpgsql
as $$
declare
  txt text := lower(coalesce(new.title, '') || ' ' || coalesce(new.description, ''));
  ttl text := lower(coalesce(new.title, ''));
  core boolean := false;
begin
  new.trilha := null;
  new.subcategoria := null;
  new.area_correlata := null;

  -- Núcleo explícito de CRM/CX/CS: não é "correlata", é a própria área.
  core :=
    ttl ~ '(^|[^a-z])crm([^a-z]|$)'
    or ttl like '%customer success%'
    or ttl like '%customer experience%'
    or ttl like '%customer service%'
    or ttl like '%customer support%'
    or ttl like '%customer care%'
    or ttl like '%customer happiness%'
    or ttl like '%sucesso do cliente%'
    or ttl like '%experiência do cliente%'
    or ttl like '%experiencia do cliente%'
    or ttl like '%marketing automation%'
    or ttl like '%marketing cloud%'
    or ttl like '%lifecycle marketing%'
    or ttl like '%retention marketing%'
    or ttl like '%jornada do cliente%'
    or ttl like '%customer journey%';

  -- 1) IA / FDE / agentes
  if txt like '%forward deployed engineer%'
     or ttl ~ '(^|[^a-z])fde([^a-z]|$)'
     or txt like '%ai agent%'
     or txt like '%ai agents%'
     or txt like '%agentic ai%'
     or txt like '%agente de ia%'
     or txt like '%agentes de ia%'
     or txt like '%agentes ia%'
     or txt like '%ai solutions architect%'
     or txt like '%ai agent architect%'
  then
    new.trilha := 'IA & Automação';
    new.subcategoria := 'FDE / AI Agents';

  elsif txt like '%conversational ai%'
     or txt like '%ia conversacional%'
     or txt like '%generative ai%'
     or txt like '%ia generativa%'
     or txt like '%llm%'
     or txt like '%prompt engineer%'
     or txt like '%chatbot%'
  then
    new.trilha := 'IA & Automação';
    new.subcategoria := 'IA Conversacional & Generativa';

  -- 2) CRM, plataformas e automação
  elsif txt ~ '(^|[^a-z])crm([^a-z]|$)'
     or txt like '%salesforce%'
     or txt like '%marketing cloud%'
     or txt like '%sfmc%'
     or txt like '%hubspot%'
     or txt like '%rd station%'
     or txt like '%braze%'
     or txt like '%insider%'
     or txt like '%martech%'
     or txt like '%marketing automation%'
     or txt like '%automação de marketing%'
     or txt like '%automacao de marketing%'
     or txt like '%customer data platform%'
     or txt like '% cdp %'
  then
    new.trilha := 'CRM & Lifecycle';
    new.subcategoria := 'CRM, Martech & Automação';

  elsif txt like '%lifecycle%'
     or txt like '%retention%'
     or txt like '%retenção%'
     or txt like '%retencao%'
     or txt like '%churn%'
     or txt like '%loyalty%'
     or txt like '%fidelidade%'
     or txt like '%fidelização%'
     or txt like '%fidelizacao%'
     or txt like '%reativação%'
     or txt like '%reativacao%'
  then
    new.trilha := 'CRM & Lifecycle';
    new.subcategoria := 'Lifecycle, Retenção & Loyalty';

  -- 3) CX / CS
  elsif txt like '%customer success%'
     or txt like '%client success%'
     or txt like '%sucesso do cliente%'
     or txt like '%cs ops%'
     or txt like '%success ops%'
     or txt like '%cs strategy%'
  then
    new.trilha := 'CX & CS';
    new.subcategoria := 'Customer Success';

  elsif txt like '%customer experience%'
     or txt like '%experiência do cliente%'
     or txt like '%experiencia do cliente%'
     or ttl ~ '(^|[^a-z])cx([^a-z]|$)'
  then
    new.trilha := 'CX & CS';
    new.subcategoria := 'Customer Experience';

  elsif txt like '%customer service%'
     or txt like '%customer support%'
     or txt like '%customer care%'
     or txt like '%customer happiness%'
     or txt like '%atendimento ao cliente%'
     or txt like '%suporte ao cliente%'
     or txt like '%relacionamento com cliente%'
     or txt like '%relacionamento com o cliente%'
     or txt like '%service desk%'
     or txt like '%ouvidoria%'
     or txt like '%reclame aqui%'
     or txt ~ '(^|[^a-z])sac([^a-z]|$)'
  then
    new.trilha := 'CX & CS';
    new.subcategoria := 'Customer Service & Support';

  elsif txt like '%onboarding%'
     or txt like '%implantação%'
     or txt like '%implantacao%'
     or txt like '%implementação%'
     or txt like '%implementacao%'
  then
    new.trilha := 'CX & CS';
    new.subcategoria := 'Onboarding & Implementation';

  elsif txt like '%customer journey%'
     or txt like '%jornada do cliente%'
     or txt like '% nps %'
     or txt like '%health score%'
     or txt like '%voz do cliente%'
     or txt like '%voice of customer%'
  then
    new.trilha := 'CX & CS';
    new.subcategoria := 'Jornada, NPS & Voz do Cliente';

  -- 4) Dados / insights
  elsif txt like '%consumer insights%'
     or txt like '%customer insights%'
     or txt like '%market insights%'
     or txt like '%inteligência de mercado%'
     or txt like '%inteligencia de mercado%'
     or txt like '%pesquisa de mercado%'
     or txt like '%customer analytics%'
     or txt like '%cx analytics%'
     or txt like '%business intelligence%'
     or txt like '%data analyst%'
     or txt like '%analista de dados%'
  then
    new.trilha := 'Dados & Insights';
    new.subcategoria := 'Insights, Pesquisa & Analytics';

  -- 5) Growth / RevOps
  elsif txt like '%revops%'
     or txt like '%revenue operations%'
     or txt like '%sales operations%'
     or txt like '%sales ops%'
  then
    new.trilha := 'Growth & Revenue';
    new.subcategoria := 'RevOps';

  elsif txt like '%growth%'
     or txt like '%acquisition%'
     or txt like '%aquisição%'
     or txt like '%aquisicao%'
     or txt like '%monetização%'
     or txt like '%monetizacao%'
     or txt like '%performance marketing%'
  then
    new.trilha := 'Growth & Revenue';
    new.subcategoria := 'Growth & Performance';

  -- 6) Produto / design
  elsif txt like '%product manager%'
     or txt like '%product owner%'
     or txt like '%produto%'
     or txt like '%product design%'
     or txt like '%designer%'
     or txt like '%service design%'
     or txt like '% ux %'
     or txt like '%user experience%'
  then
    new.trilha := 'Produto & Design';
    new.subcategoria := 'Produto, UX & Design';

  -- 7) Operações / estratégia
  elsif txt like '%operations%'
     or txt like '%operações%'
     or txt like '%operacoes%'
     or txt like '%processos%'
     or txt like '%strategy%'
     or txt like '%estratégia%'
     or txt like '%estrategia%'
     or txt like '%projetos%'
     or txt like '%project manager%'
     or txt like '%supervisor%'
     or txt like '%coordenação%'
     or txt like '%coordenacao%'
  then
    new.trilha := 'Operações & Estratégia';
    new.subcategoria := 'Operações, Processos & Gestão';

  -- 8) Marketing geral
  elsif txt like '%marketing%'
     or txt like '%comunicação%'
     or txt like '%comunicacao%'
     or txt like '%conteúdo%'
     or txt like '%conteudo%'
     or txt like '%campanha%'
  then
    new.trilha := 'Marketing & Conteúdo';
    new.subcategoria := 'Marketing & Comunicação';

  -- Fallback pela categoria principal para manter compatibilidade.
  elsif lower(coalesce(new.category, '')) = 'cxcs' then
    new.trilha := 'CX & CS';
    new.subcategoria := 'CX/CS Geral';

  elsif lower(coalesce(new.category, '')) = 'crm' then
    new.trilha := 'CRM & Lifecycle';
    new.subcategoria := 'CRM Geral';
  end if;

  if new.trilha is not null then
    new.area_correlata := not core;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_taxonomia_vagas_scraper on public.vagas_scraper;
create trigger trg_taxonomia_vagas_scraper
before insert or update of title, description, category
on public.vagas_scraper
for each row execute function public.classificar_taxonomia_vaga();

drop trigger if exists trg_taxonomia_vagas_crm on public.vagas_crm;
create trigger trg_taxonomia_vagas_crm
before insert or update of title, description, category
on public.vagas_crm
for each row execute function public.classificar_taxonomia_vaga();

create index if not exists idx_vagas_scraper_trilha on public.vagas_scraper(trilha);
create index if not exists idx_vagas_scraper_subcategoria on public.vagas_scraper(subcategoria);
create index if not exists idx_vagas_scraper_area_correlata on public.vagas_scraper(area_correlata);

create index if not exists idx_vagas_crm_trilha on public.vagas_crm(trilha);
create index if not exists idx_vagas_crm_subcategoria on public.vagas_crm(subcategoria);
create index if not exists idx_vagas_crm_area_correlata on public.vagas_crm(area_correlata);

-- Reclassifica o histórico sem alterar a categoria principal.
update public.vagas_scraper set category = category;
update public.vagas_crm set category = category;
