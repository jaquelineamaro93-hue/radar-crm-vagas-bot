-- Radar de Vagas: versioned classification rules, applied to Supabase production 2026-10-13.
-- Existing non-null categories are preserved. Out-of-scope and ambiguous jobs are retained.
create or replace function public.classify_radar_job_title(p_title text) returns text language sql immutable as $$
select case
when coalesce(p_title,'') ~* '(sobrancelh|manicure|nail designer|designer de interiores|designer t[eê]xtil|arquitetura|engenheiro eletricista|manuten[cç][aã]o|accounting|financial analyst|compliance analyst|ag[eê]ncia de viagens|special education|cybersecurity)' then 'fora_escopo'
when coalesce(p_title,'') ~* '(ux|ui designer|service.now ux|service designer|product design|designer de interface)' then 'designer'
when coalesce(p_title,'') ~* '(sales.?ops|sales operations|sales enablement|sales manager|supervisor comercial|account executive|pre.sales|business operations|sales audit)' then 'salesops'
when coalesce(p_title,'') ~* '(\mABM\M|account.based marketing|brand|creative strategist|community manager|creator program|content|marketing|digital rewards|market manager|merchandising)' then 'marketing'
when coalesce(p_title,'') ~* '(data intelligence|business analyst|analytics|data science|data engineer|data architect)' then 'data'
when coalesce(p_title,'') ~* '(automa[cç][aã]o|automation|programador de clp|\mCLP\M)' then 'automacao'
when coalesce(p_title,'') ~* '(support engagement|customer|atendimento|\mCRC\M)' then 'cxcs'
when coalesce(p_title,'') ~* '(product manager|product owner|product lead)' then 'po_pm'
when coalesce(p_title,'') ~* '(artificial intelligence|genai|\mAI\M|intelig[eê]ncia artificial)' then 'ia'
when coalesce(p_title,'') ~* '(tech lead|developer|desenvolvedor|engenheiro de software|solution architect|technical)' then 'tech'
when coalesce(p_title,'') ~* '(revenue operations|revops|growth operations)' then 'revops'
when coalesce(p_title,'') ~* '(\mCRM\M|salesforce|hubspot|braze|marketing cloud|lifecycle)' then 'crm'
else 'revisao_escopo' end $$;
create or replace function public.radar_auto_classify_category() returns trigger language plpgsql as $$
begin
if new.category is null or btrim(new.category)='' then
new.category := public.classify_radar_job_title(coalesce(nullif(new.title,''),new.cargo));
end if;
return new;
end $$;
drop trigger if exists trg_radar_auto_classify_category on public.vagas_crm;
create trigger trg_radar_auto_classify_category before insert or update of title,cargo,category on public.vagas_crm for each row execute function public.radar_auto_classify_category();
update public.vagas_crm set category=public.classify_radar_job_title(coalesce(nullif(title,''),cargo)) where category is null or btrim(category)='';
