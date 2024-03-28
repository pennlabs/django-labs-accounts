import json

from django.test import TestCase

from analytics.analytics import AnalyticsTxn, Product


class AnalyticsTxnTestCase(TestCase):
    def test_analytics_txn(self):
        data = {
            "product": Product.MOBILE_BACKEND,
            "pennkey": None,
            "data": {"key": "backend", "value": "data"},
        }

        txn = AnalyticsTxn(**data)
        data_json = txn.to_json()
        data_dict = json.loads(data_json)

        self.assertEqual("MOBILE_BACKEND", data_dict["product"])
        self.assertIsNone(data_dict["pennkey"])
        self.assertIn("timestamp", data_dict)
