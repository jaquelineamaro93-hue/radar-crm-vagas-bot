"""Contrato das novas fontes: datas comprovadas, links autenticos e escopo."""
import unittest
from datetime import datetime, timezone, timedelta

from bs4 import BeautifulSoup

from scrapers.startupjobs import _feed_entries, _safe_link
from scrapers.vagasremotas import _parse_job, _list_links
from scrapers.vagascom import _card_publication, SOURCE as VAGAS_SOURCE
from scrapers import ALL_SCRAPERS


class NewSourceTests(unittest.TestCase):
    def test_startup_rss_usa_data_real_e_link_autorizado(self):
        now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        feed = ("<rss><channel><item><title>Customer Success Manager</title>"
                "<link>https://startup.jobs/jobs/customer-success-123</link>"
                f"<pubDate>{now}</pubDate><description>Brasil</description>"
                "</item></channel></rss>")
        rows = list(_feed_entries(feed))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Customer Success Manager")
        self.assertTrue(rows[0][2])
        self.assertIsNone(_safe_link("https://outraempresa.example/jobs/123"))

    def test_vagasremotas_nao_inventa_data_para_uma_vaga(self):
        html = ('<main><h1>Analista de CRM</h1><h4>Empresa X</h4>'
                '<div>Descrição e responsabilidades sem data de publicação</div></main>')
        self.assertIsNone(_parse_job(html, "https://vagasremotas.com.br/vagas-home-office-remoto/crm/"))
        with_date = html.replace(
            "<div>Descrição", "<div>Data Postada: Posted 2 days ago</div><div>Descrição"
        )
        vaga = _parse_job(with_date, "https://vagasremotas.com.br/vagas-home-office-remoto/crm/")
        self.assertEqual(vaga["category"], "crm")
        self.assertEqual(vaga["source"], "VagasRemotas.com.br")

    def test_links_vagasremotas_ignora_paginas_de_navegacao(self):
        html = ('<a href="/vagas-home-office-remoto/">Lista</a>'
                '<a href="/vagas-home-office-remoto/analista-crm/">Vaga</a>'
                '<a href="https://outro.example/vagas-home-office-remoto/falsa/">Falsa</a>')
        self.assertEqual(
            list(_list_links(html)),
            ["https://vagasremotas.com.br/vagas-home-office-remoto/analista-crm/"]
        )

    def test_vagascom_voce_data_do_proprio_card(self):
        now = datetime.now(timezone.utc)
        html = ('<li><h2 class="cargo">'
                '<a class="link-detalhes-vaga" href="/v123">Analista de CRM</a></h2>'
                '<div class="data">Ontem</div></li>')
        link = BeautifulSoup(html, "html.parser").select_one("a.link-detalhes-vaga")
        date = datetime.fromisoformat(_card_publication(link))
        self.assertLess(now - date, timedelta(days=3))
        self.assertEqual(VAGAS_SOURCE, "Vagas.com Você")

    def test_orquestrador_unico_inclui_ambas_as_novas_fontes(self):
        names = {f.__module__.split(".")[-1] for f in ALL_SCRAPERS}
        self.assertIn("startupjobs", names)
        self.assertIn("vagasremotas", names)
        self.assertIn("vagascom", names)


if __name__ == "__main__":
    unittest.main()
