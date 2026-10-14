import unittest
from bs4 import BeautifulSoup
from scrapers.base import extract_publication_date
from scrapers.gupy import API_URL as GUPY_API_URL, _verified_open
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from supabase_sync import sync_vaga_crm


class DateEvidenceTests(unittest.TestCase):
    def test_gupy_public_endpoint(self):
        self.assertEqual(GUPY_API_URL, 'https://portal.gupy.io/api/job-search/jobs')

    def test_nao_inventa_data_por_palavra_no_titulo(self):
        card = BeautifulSoup(
            '<article><h2>Marketing de hoje e CRM</h2></article>', 'html.parser'
        ).article
        self.assertIsNone(extract_publication_date(card))

    def test_aceita_data_documentada_em_time(self):
        card = BeautifulSoup(
            '<article><time datetime="2026-10-14">Publicada</time></article>',
            'html.parser',
        ).article
        self.assertTrue(extract_publication_date(card).startswith('2026-10-14'))

    def test_rejeita_atributo_de_data_invalido(self):
        card = BeautifulSoup(
            '<article data-date="ontem"><h2>CRM</h2></article>', 'html.parser'
        ).article
        self.assertIsNone(extract_publication_date(card))


class ActiveJobsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
        self.vaga = {
            "jobUrl": "https://empresa.gupy.io/job/valido",
            "applicationDeadline": "2026-11-10T00:00:00.000Z",
            "publishedDate": "2026-10-10T00:00:00Z",
        }

    def test_gupy_prazo_futuro_pode_receber_status_aberta(self):
        self.assertTrue(_verified_open(self.vaga, self.now))

    def test_gupy_prazo_vencido_ou_fechado_ou_ausente_rejeitado(self):
        for override in (
            {"applicationDeadline": "2026-10-12T00:00:00Z"},
            {"applicationDeadline": None},
            {"isOpen": False},
            {"jobStatus": "closed"},
            {"jobUrl": "https://example.com/job/valido"},
        ):
            with self.subTest(override=override):
                self.assertFalse(_verified_open({**self.vaga, **override}, self.now))

    def test_supabase_so_confirma_aberta_com_evidencia_gupy(self):
        base = {
            "title": "Analista CRM", "category": "crm",
            "url": "https://empresa.gupy.io/job/123",
            "published_at": "2026-10-14T00:00:00Z", "source": "Gupy",
        }
        with patch("supabase_sync.SUPABASE_URL", "https://example.invalid"), \
             patch("supabase_sync.SUPABASE_KEY", "test-placeholder"), \
             patch("supabase_sync.requests.post") as post:
            post.return_value.ok = True
            for vaga in (
                base,
                {**base, "source": "LinkedIn",
                 "availability_evidence": "gupy_open_deadline",
                 "availability_checked_at": self.now.isoformat()},
                {**base, "availability_evidence": "gupy_open_deadline",
                 "availability_checked_at": self.now.isoformat()},
            ):
                self.assertTrue(sync_vaga_crm(vaga))
                payload = post.call_args.kwargs["json"]
                if vaga["source"] == "Gupy" and vaga.get("availability_evidence"):
                    self.assertEqual(payload["availability_status"], "listed")
                else:
                    self.assertNotIn("availability_status", payload)


if __name__ == "__main__":
    unittest.main()
