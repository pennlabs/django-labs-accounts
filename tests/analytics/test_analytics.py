import json

from django.test import TestCase

from analytics.analytics import AnalyticsTxn, Product, LabsAnalytics
from identity.identity import attest


class AnalyticsTxnTestCase(TestCase):
    def test_analytics_txn(self):
        data = {
            "product": Product.MOBILE_BACKEND,
            "pennkey": None,
            "data": [{"key": "backend", "value": "data"}],
        }

        txn = AnalyticsTxn(**data)
        data_json = txn.to_json()
        # data_dict = json.dumps(data_json)

        self.assertEqual(Product.MOBILE_BACKEND.value, int(data_json["product"]))
        self.assertIsNone(data_json["pennkey"])
        self.assertIn("timestamp", data_json)

class AnalyticsSubmission(TestCase):

    # TODO: Add mocked test cases for Analytics

    def setUp(self):
        attest()
        self.analytics_wrapper = LabsAnalytics()

    def test_submit(self):
        data = {
            "product": Product.MOBILE_BACKEND,
            "pennkey": "hi",
            "data": [{"key": "backend", "value": "data"}],
        }

        txn = AnalyticsTxn(**data)

        self.analytics_wrapper.submit(txn)
        assert False