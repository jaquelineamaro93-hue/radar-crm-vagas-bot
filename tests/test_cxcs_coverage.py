import unittest

from scrapers.base import classify
from config import (
    CXCS_SEARCH_TERMS,
    NEW_CXCS_TITLES,
    CXCS_EXTRA_TITLES_20261001,
)
from scrapers import linkedin, catho, indeed, gupy, vagascom, infojobs


class CxCsCoverageTests(unittest.TestCase):
    def test_all_known_cxcs_titles_are_classified_as_cxcs(self):
        titles = NEW_CXCS_TITLES + CXCS_EXTRA_TITLES_20261001
        self.assertGreaterEqual(len(titles), 180)

        for title in titles:
            with self.subTest(title=title):
                self.assertEqual(classify(title), "cxcs")

    def test_priority_variations_are_cxcs(self):
        samples = [
            "Manager, Customer Success",
            "Customer Service Specialist",
            "Supervisor de Sucesso do Cliente",
            "Analista de Relacionamento Jr | Customer Experience - CX",
            "CX | Assistente de Atendimento ao Cliente (TEMPORÁRIO)",
            "Onboarding Specialist - Customer Success Analyst (Remote)",
        ]
        for title in samples:
            with self.subTest(title=title):
                self.assertEqual(classify(title), "cxcs")

    def test_crm_stays_crm(self):
        self.assertEqual(classify("Analista de CRM"), "crm")
        self.assertEqual(classify("Salesforce Marketing Cloud Specialist"), "crm")

    def test_cx_searches_run_first(self):
        first_linkedin = [item[0] for item in linkedin.SEARCHES[: len(CXCS_SEARCH_TERMS)]]
        self.assertEqual(first_linkedin, CXCS_SEARCH_TERMS)

        first_catho = catho.SEARCHES[: len(CXCS_SEARCH_TERMS)]
        expected_catho = [term.casefold().replace(" ", "-") for term in CXCS_SEARCH_TERMS]
        self.assertEqual(first_catho, expected_catho)

        first_indeed = [item[0] for item in indeed.SEARCHES[: len(CXCS_SEARCH_TERMS)]]
        self.assertEqual(first_indeed, CXCS_SEARCH_TERMS)

        first_vagas = vagascom.SEARCHES[: len(CXCS_SEARCH_TERMS)]
        expected_vagas = [
            "vagas-de-" + term.casefold().replace(" ", "-")
            for term in CXCS_SEARCH_TERMS
        ]
        self.assertEqual(first_vagas, expected_vagas)

        first_infojobs = [item[0] for item in infojobs.SEARCHES[: len(CXCS_SEARCH_TERMS)]]
        expected_infojobs = [
            "vagas-de-emprego-" + term.casefold().replace(" ", "-") + "-trabalho-home-office"
            for term in CXCS_SEARCH_TERMS
        ]
        self.assertEqual(first_infojobs, expected_infojobs)

    def test_gupy_uses_compact_discovery_instead_of_every_keyword(self):
        # Regressão: o scraper não deve fazer uma chamada para cada termo de
        # KEYWORDS["crm"], pois isso estoura o tempo de execução serverless.
        source = open("scrapers/gupy.py", encoding="utf-8").read()
        self.assertNotIn('KEYWORDS.get("crm", []) + CXCS_SEARCH_TERMS', source)
        self.assertIn("crm_searches + CXCS_SEARCH_TERMS", source)


if __name__ == "__main__":
    unittest.main()
