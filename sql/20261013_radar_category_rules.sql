-- Production rule revision: preserve every collected job title, including beauty/interior design.
-- 'outros' is a valid inclusive category, not a rejection status.
create or replace function public.classify_radar_job_title(p_title text) returns text language sql immutable as $$
select case
when coalesce(p_title,'') ~* '(sobrancelh|manicure|nail designer|designer de interiores|designer t[eê]xtil|designer gr[aá]fic|web designer|designer instrucional|designer de convers[aã]o|ux writer|ux/ui|ux designer|ui designer|product design|designer de produto|designer)' then 'designer'
when coalesce(p_title,'') ~* '(sales.?ops|sales operations|sales enablement|sales manager|supervisor comercial|account executive|pre.sales|business operations|sales audit)' then 'salesops'
when coalesce(p_title,'') ~* '(\\mABM\\M|account.based marketing|brand|creative strategist|community manager|creator program|content|marketing|digital rewards|market manager|merchandising)' then 'marketing'
when coalesce(p_title,'') ~* '(data intelligence|business analyst|analytics|data science|data engineer|data architect)' then 'data'
when coalesce(p_title,'') ~* '(automa[cç][aã]o|automation|programador de clp|\\mCLP\\M)' then 'automacao'
when coalesce(p_title,'') ~* '(support engagement|customer|atendimento|\\mCRC\\M)' then 'cxcs'
when coalesce(p_title,'') ~* '(product manager|product owner|product lead)' then 'po_pm'
when coalesce(p_title,'') ~* '(artificial intelligence|genai|\\mAI\\M|intelig[eê]ncia artificial)' then 'ia'
when coalesce(p_title,'') ~* '(tech lead|developer|desenvolvedor|engenheiro de software|solution architect|technical|cybersecurity)' then 'tech'
when coalesce(p_title,'') ~* '(revenue operations|revops|growth operations)' then 'revops'
when coalesce(p_title,'') ~* '(\\mCRM\\M|salesforce|hubspot|braze|marketing cloud|lifecycle)' then 'crm'
else 'outros' end $$;
create or replace function public.radar_auto_classify_category() returns trigger language plpgsql as $$
begin
if new.category is null or btrim(new.category)='' then
new.category := public.classify_radar_job_title(coalesce(nullif(new.title,''),new.cargo));
end if;
return new;
end $$;
drop trigger if exists trg_radar_auto_classify_category on public.vagas_crm;
create trigger trg_radar_auto_classify_category before insert or update of title,cargo,category on public.vagas_crm for each row execute function public.radar_auto_classify_category();
update public.vagas_crm set category=public.classify_radar_job_title(coalesce(nullif(title,''),cargo)) where category in ('fora_escopo','revisao_escopo') or category is null;
