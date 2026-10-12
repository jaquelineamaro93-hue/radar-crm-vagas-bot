import unittest

from scrapers.base import classify
from config import CXCS_SEARCH_TERMS
from scrapers import linkedin, catho, indeed, vagascom, infojobs
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

    def test_all_requested_cxcs_searches_exist_without_category_priority(self):
        # Inclusion is required, but no profession gets a privileged first position.
        self.assertTrue(set(CXCS_SEARCH_TERMS).issubset({
            item[0] for item in linkedin.SEARCHES
        }))
        self.assertTrue({
            term.casefold().replace(" ", "-") for term in CXCS_SEARCH_TERMS
        }.issubset(set(catho.SEARCHES)))
        self.assertTrue(set(CXCS_SEARCH_TERMS).issubset({
            item[0] for item in indeed.SEARCHES
        }))
        self.assertTrue({
            "vagas-de-" + term.casefold().replace(" ", "-")
            for term in CXCS_SEARCH_TERMS
        }.issubset(set(vagascom.SEARCHES)))
        self.assertTrue({
            "vagas-de-emprego-" + term.casefold().replace(" ", "-") + "-trabalho-home-office"
            for term in CXCS_SEARCH_TERMS
        }.issubset({item[0] for item in infojobs.SEARCHES}))

    def test_other_categories_remain_available(self):
        # Regression: CRM, design and other roles must not be removed.
        self.assertTrue(any("crm" in item[0].casefold() for item in linkedin.SEARCHES))
        self.assertTrue(any("designer" in item[0].casefold() for item in infojobs.SEARCHES))
        self.assertTrue(any("crm" in item for item in vagascom.SEARCHES))


if __name__ == "__main__":
    unittest.main()
