"""Testes da selecao de lotes do radar, sem rede ou banco."""
import unittest
from unittest.mock import patch

from search_plan import _balanced_terms, select_search_batch


class SearchPlanTests(unittest.TestCase):
    def test_intercala_familias_sem_omitir_termos(self):
        terms = [
            "analista crm", "gerente crm", "coordenador crm",
            "customer success", "customer experience",
            "marketing", "growth", "revops",
            "salesforce", "hubspot", "data analytics",
            "product designer", "quality assurance", "marketing automation",
        ]
        ordered = _balanced_terms(terms)
        self.assertEqual(set(ordered), set(terms))
        self.assertEqual(len(ordered), len(terms))
        self.assertGreater(len(set(ordered[:8]).intersection(set(terms[3:]))), 3)

    def test_cursor_progride_ate_cobrir_o_catalogo(self):
        terms = ["crm " + str(i) for i in range(48)]
        state = {"cursor": 0}

        def claim(source, total, batch):
            start = state["cursor"]
            state["cursor"] = (start + batch) % total
            return start, True

        visited = set()
        with patch("search_plan._claim_offset", side_effect=claim):
            for _ in range(3):
                jobs, progress = select_search_batch(terms, source="teste", limit=16)
                self.assertEqual(len(jobs), 16)
                self.assertTrue(progress["persisted"])
                visited.update(jobs)
        self.assertEqual(visited, set(terms))
        self.assertEqual(state["cursor"], 0)

    def test_cap_de_buscas_impede_execucao_ilimitada(self):
        terms = ["crm " + str(i) for i in range(100)]
        with patch("search_plan._claim_offset", return_value=(0, True)):
            jobs, progress = select_search_batch(terms, source="teste", limit=999)
        self.assertEqual(len(jobs), 40)
        self.assertEqual(progress["next_offset"], 40)


if __name__ == "__main__":
    unittest.main()
