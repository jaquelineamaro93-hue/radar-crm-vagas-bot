import unittest
from bs4 import BeautifulSoup
from scrapers.base import extract_publication_date


class DateEvidenceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
