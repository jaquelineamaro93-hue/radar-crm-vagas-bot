import unittest
from datetime import datetime, timezone, timedelta

from search_plan import select_searches
from scrapers.base import is_recent
from supabase_sync import _taxonomia, _metadata
from otw_sync import _source_key, _consent, _public_payload


class RadarIntegrity(unittest.TestCase):
    def test_date_window_strict(self):
        self.assertFalse(is_recent(None,14))
        self.assertFalse(is_recent('não informado',14))
        self.assertFalse(is_recent((datetime.now(timezone.utc)-timedelta(days=15)).isoformat(),14))
        self.assertTrue(is_recent((datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),14))
    def test_categories_without_priority(self):
        terms=['crm','customer success','marketing','salesforce','hubspot','growth','revops',
               'analista de dados','ia','product designer','product owner','qa','automation','ecommerce']
        selected={tuple(select_searches(terms,source='source'+str(i),limit=5,day_index=739908)) for i in range(8)}
        self.assertTrue(len(selected)>=3)
        self.assertTrue(any('crm' in group for group in selected))
        self.assertTrue(any('product designer' in group for group in selected))
    def test_tags_keep_crm_and_design(self):
        self.assertEqual(_taxonomia({'category':'crm','title':'Analista CRM'})[0],'crm')
        self.assertEqual(_taxonomia({'category':'designer','title':'Product Designer'})[0],'product-design')
        self.assertEqual(_taxonomia({'category':'cxcs','title':'Customer Success Manager'})[0],'customer-success')
    def test_normalize_only_explicit_modality(self):
        self.assertIsNone(_metadata({'title':'Analista CRM','location':'São Paulo'})[0])
        self.assertEqual(_metadata({'title':'Analista CRM','location':'Remoto'})[0],'Remoto')
    def test_otw_stable_source_key(self):
        a={'Nome':'Ana Exemplo','Linkedin':'https://linkedin.com/in/ana'}
        self.assertEqual(_source_key(a),_source_key(a))
        self.assertFalse(_consent(a))
        a['Autorizo divulgação dos meus dados']='Sim'
        self.assertTrue(_consent(a))
        self.assertEqual(_public_payload(a,_source_key(a))['nome'],'Ana Exemplo')


if __name__=='__main__':
    unittest.main()
