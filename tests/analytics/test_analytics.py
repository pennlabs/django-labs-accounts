import random
from unittest import mock

from django.test import TestCase

from analytics.analytics import (
    AnalyticsTxn,
    LabsAnalyticsRecorder,
    Product,
    get_analytics_recorder,
)


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
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder._refresh_expires_at")
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder._refresh_headers")
    def setUp(self, mock_expires_at, mock_headers):
        # NOTE: use attest this for real testing
        # from identity.identity import attest
        # attest()
        self.analytics_wrapper = get_analytics_recorder(Product.MOBILE_BACKEND)

        # should be this because mocking lets the refresh stuff not error
        self.assertIsInstance(self.analytics_wrapper, LabsAnalyticsRecorder)

        self.NUM_TRIES = 1000

    def rand_int(self):
        return random.randint(1, self.NUM_TRIES)

    def generate_data(self):
        return {
            "product": Product.MOBILE_BACKEND,
            "pennkey": None,
            "data": [{"key": f"{self.rand_int()}", "value": f"{self.rand_int()}"}],
        }

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_submit(self, mock_submit):
        for _ in range(self.NUM_TRIES):
            txn = AnalyticsTxn(**self.generate_data())
            self.analytics_wrapper.submit(txn)

        self.assertEqual(self.NUM_TRIES, mock_submit.call_count)

        self.analytics_wrapper.executor.shutdown(wait=True)
