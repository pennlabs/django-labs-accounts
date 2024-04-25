from django.test import TestCase

from analytics.analytics import AnalyticsTxn, LabsAnalytics, Product
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
            "pennkey": "judtin",
            "data": [{"key": "backend", "value": "some data"}],
        }

        for _ in range(20):
            data["product"] = Product((data["product"].value + 1) % len(Product))
            txn = AnalyticsTxn(**data)
            self.analytics_wrapper.submit(txn)

        self.analytics_wrapper.executor.shutdown(wait=True)

        assert False
