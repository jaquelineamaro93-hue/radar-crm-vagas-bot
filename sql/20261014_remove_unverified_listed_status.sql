-- Corrige o status de vagas publicadas pelo bot sem validação independente.
-- Não apaga vagas, URLs, candidaturas, referências ou histórico.
-- A execução foi aplicada em produção em 2026-10-14 (45 registros alterados).
UPDATE public.vagas_crm
SET availability_status = 'unverified'
WHERE availability_status = 'listed'
  AND availability_checked_at IS NULL;
