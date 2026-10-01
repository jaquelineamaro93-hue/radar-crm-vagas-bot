import unittest

from scrapers.base import classify
from config import CXCS_SEARCH_TERMS
from scrapers import linkedin, catho, indeed
from supabase_sync import _matches_crm_ecosystem


class CxCsCoverageTests(unittest.TestCase):
    def test_priority_titles_are_cxcs(self):
        samples = [
            "Customer Success Manager",
            "Customer Experience Manager",
            "Customer Success Manager- Marketing Cloud",
            "Analista de Customer Service Pleno",
            "Analista de Consumer Market Insights Sênior (CMI)",
            "Analista de Operações Pleno",
            "Sr. CS Strategy & Operations Analyst",
            "Analista de NPS (Customer Success)",
            "Analista de Qualidade na Experiência do Cliente & Onboarding",
        ]
        for title in samples:
            with self.subTest(title=title):
                self.assertEqual(classify(title), "cxcs")

    def test_crm_stays_crm(self):
        self.assertEqual(classify("Analista de CRM"), "crm")
        self.assertEqual(classify("Salesforce Marketing Cloud Specialist"), "crm")

    def test_cxcs_is_synced_to_dashboard(self):
        self.assertTrue(_matches_crm_ecosystem({
            "title": "Analista de Sucesso do Cliente",
            "category": "cxcs",
            "description": "",
        }))

    def test_cx_searches_run_first(self):
        first_linkedin = [item[0] for item in linkedin.SEARCHES[: len(CXCS_SEARCH_TERMS)]]
        self.assertEqual(first_linkedin, CXCS_SEARCH_TERMS)

        first_catho = catho.SEARCHES[: len(CXCS_SEARCH_TERMS)]
        expected_catho = [term.casefold().replace(" ", "-") for term in CXCS_SEARCH_TERMS]
        self.assertEqual(first_catho, expected_catho)

        first_indeed = [item[0] for item in indeed.SEARCHES[: len(CXCS_SEARCH_TERMS)]]
        self.assertEqual(first_indeed, CXCS_SEARCH_TERMS)


if __name__ == "__main__":
    unittest.main()
