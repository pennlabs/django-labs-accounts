from abc import ABC
from unittest import mock

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.analytics import Product, get_analytics_recorder
from analytics.entries import FuncEntry, UnaryFuncEntry, ViewEntry


User = get_user_model()


class FakeRequest(HttpRequest):
    def __init__(
        self,
        method="FAKE_METHOD",
        view_name="FAKE_VIEW_NAME",
    ):
        super().__init__()
        self.method = method

        self.resolver_match = mock.MagicMock()
        self.resolver_match.view_name = view_name


class AnalyticsRecorderBaseTestCase(TestCase, ABC):
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder._refresh_expires_at")
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder._refresh_headers")
    def setUp(self, mock_expires_at, mock_headers):
        self.analytics_wrapper = get_analytics_recorder(Product.MOBILE_BACKEND)

    def verify_transaction(self, submit_transaction, datas):
        self.assertEqual(submit_transaction.call_count, 1)
        txn = submit_transaction.call_args[0][0]
        self.assertEqual(txn.product, Product.MOBILE_BACKEND)
        self.assertListEqual(txn.data, datas)

    def verify_transaction_singleton(self, submit_transaction, key, value):
        self.verify_transaction(submit_transaction, [{"key": key, "value": value}])


class AnalyticsRecorderAPIViewTestCase(AnalyticsRecorderBaseTestCase):
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_basic_api_view(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(ViewEntry())
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(submit_transaction, "FAKE_VIEW_NAME.get", "1")

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_name(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(ViewEntry(name="my_entry"))
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(
            submit_transaction, "FAKE_VIEW_NAME.my_entry.get", "1"
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_value(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(
            ViewEntry(name="my_entry", value="custom_value")
        )
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(
            submit_transaction, "FAKE_VIEW_NAME.my_entry.get", "custom_value"
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_get_value(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(
            ViewEntry(
                name="my_entry", get_value=lambda req, res: req.method + ";" + res.data
            )
        )
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(
            submit_transaction, "FAKE_VIEW_NAME.my_entry.get", "GET;Hello, world!"
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_get_value_use_before(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(
            ViewEntry(
                name="my_entry",
                compute_before=lambda: User.objects.count(),
                get_value_use_before=lambda req, res, b4: b4,
            )
        )
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(
            submit_transaction, "FAKE_VIEW_NAME.my_entry.get", "0"
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_filter_do_record(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(
            ViewEntry(filter_do_record=lambda req, res: req.method == "POST")
        )
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        view = BasicAPIView.as_view()
        response = view(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        self.assertEqual(submit_transaction.call_count, 2)

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_record_on_failure(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(ViewEntry(filter_do_record=None))
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        view = BasicAPIView.as_view()
        response = view(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        self.assertEqual(submit_transaction.call_count, 3)

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_view_specify_methods(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(
            ViewEntry(filter_do_record=None, methods=["POST"])
        )
        class BasicAPIView(APIView):
            def get(self, request):
                return Response("Hello, world!")

        view = BasicAPIView.as_view()
        response = view(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        self.assertEqual(submit_transaction.call_count, 2)

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_basic_view_set(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(ViewEntry())
        class BasicViewSet(viewsets.ModelViewSet):
            def list(self, request):
                return Response("Hello, world!")

        response = BasicViewSet.as_view({"get": "list"})(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(submit_transaction, "FAKE_VIEW_NAME.get", "1")

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_view_set_specify_actions(self, submit_transaction):
        @self.analytics_wrapper.record_apiview(
            ViewEntry(filter_do_record=None, actions=["list"])
        )
        class BasicViewSet(viewsets.ModelViewSet):
            def list(self, request):
                return Response("Hello, world!")

        view = BasicViewSet.as_view({"get": "list"})
        response = view(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        response = view(FakeRequest("POST"))
        self.assertEqual(response.status_code, 405)

        self.assertEqual(submit_transaction.call_count, 1)


class AnalyticsRecorderAPIFunctionTestCase(AnalyticsRecorderBaseTestCase):
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_basic_api_function(self, submit_transaction):
        class BasicAPIView(APIView):
            @self.analytics_wrapper.record_api_function(FuncEntry())
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(submit_transaction, "FAKE_VIEW_NAME.get", "1")

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_api_function_get_value(self, submit_transaction):
        class BasicAPIView(APIView):
            @self.analytics_wrapper.record_api_function(
                FuncEntry(
                    name="my_entry",
                    get_value=lambda args, res: f"{len(args[0].kwargs)};"
                    + f"{args[1].method};{res.data}",
                )
            )
            def get(self, request):
                return Response("Hello, world!")

        response = BasicAPIView.as_view()(FakeRequest("GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Hello, world!")

        self.verify_transaction_singleton(
            submit_transaction, "FAKE_VIEW_NAME.my_entry.get", "0;GET;Hello, world!"
        )


class AnalyticsRecorderFunctionTestCase(AnalyticsRecorderBaseTestCase):
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_basic_function(self, submit_transaction):
        @self.analytics_wrapper.record_function(FuncEntry())
        def test_func(arg1, arg2, *args, **kwargs):
            return arg1 + arg2

        test_func(1, 2)
        self.verify_transaction_singleton(
            submit_transaction,
            "tests.analytics.test_analytics_recorder.AnalyticsRecorderFunctionTestCase."
            "test_basic_function.<locals>.test_func",
            "1",
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_function_get_value(self, submit_transaction):
        @self.analytics_wrapper.record_function(
            FuncEntry(name="my_entry", get_value=lambda args, ret: f"{args};{ret}")
        )
        def test_func(arg1, arg2, *args, **kwargs):
            return arg1 + arg2

        test_func(1, 2, "extra", "params", these="are", ignored="in logging")
        self.verify_transaction_singleton(
            submit_transaction,
            "tests.analytics.test_analytics_recorder.AnalyticsRecorderFunctionTestCase."
            "test_function_get_value.<locals>.test_func.my_entry",
            "(1, 2);3",
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_function_get_value_with_args(self, submit_transaction):
        @self.analytics_wrapper.record_function(
            FuncEntry(
                name="my_entry", get_value_with_args=lambda arg1, arg2: f"{arg1};{arg2}"
            )
        )
        def test_func(arg1, arg2, *args, **kwargs):
            return arg1 + arg2

        test_func(1, 2, "extra", "params", these="are", ignored="in logging")
        self.verify_transaction_singleton(
            submit_transaction,
            "tests.analytics.test_analytics_recorder.AnalyticsRecorderFunctionTestCase."
            "test_function_get_value_with_args.<locals>.test_func.my_entry",
            "1;2",
        )

    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_function_unary(self, submit_transaction):
        @self.analytics_wrapper.record_function(
            UnaryFuncEntry(name="my_entry", get_value=lambda arg, ret: f"{arg};{ret}")
        )
        def test_func(arg1, *args, **kwargs):
            return "ret!"

        test_func(1, "extra", "params", these="are", ignored="in logging")
        self.verify_transaction_singleton(
            submit_transaction,
            "tests.analytics.test_analytics_recorder.AnalyticsRecorderFunctionTestCase."
            "test_function_unary.<locals>.test_func.my_entry",
            "1;ret!",
        )


class AnalyticsRecorderLibraryDefinedEntries(AnalyticsRecorderBaseTestCase):
    @mock.patch("analytics.analytics.LabsAnalyticsRecorder.submit_transaction")
    def test_timing_entry(self, submit_transaction):
        @self.analytics_wrapper.record_function(FuncEntry.time)
        def test_func(arg1, *args, **kwargs):
            return "ret!"

        test_func(1)
        self.assertEqual(submit_transaction.call_count, 1)
        microseconds_delta = int(submit_transaction.call_args[0][0].data[0]["value"])
        self.assertLessEqual(
            microseconds_delta, 100
        )  # we expect this function's time to be fast
