import json
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from functools import wraps
from string import Template
from typing import Any, Callable, List, Optional, Type

from django.utils import timezone
from django.utils.termcolors import colorize
from requests import Session
from rest_framework.views import APIView

from analytics.entries import (
    AnalyticsEntry,
    FuncEntry,
    FunctionParam,
    FunctionReturn,
    UnaryFuncEntry,
    ViewEntry,
)
from identity.identity import _refresh_if_outdated, container


class Product(IntEnum):
    OTHER = 0
    MOBILE_IOS = 1
    MOBILE_ANDROID = 2
    MOBILE_BACKEND = 3
    PORTAL = 4
    PCR = 5
    PDP = 6
    PCA = 7
    PCP = 8
    OHQ = 9
    CLUBS = 10

    def __str__(self):
        return self.name


class AnalyticsTxn:
    def __init__(
        self,
        product: Product,
        pennkey: Optional[str],
        timestamp=None,
        data=None,
    ):
        self.product = product.value
        self.pennkey = pennkey
        self.timestamp = (timestamp or timezone.now()).timestamp()
        self.data = data or []

    def to_json(self):
        return json.loads(json.dumps(vars(self)))


class AnalyticsSubmitter(ABC):
    def __init__(self, default_product: Product):
        self.default_product = default_product

    @abstractmethod
    def submit_transaction(self, txn: AnalyticsTxn):
        pass

    def submit(
        self,
        data: List[dict],
        product: Optional[Product] = None,
        pennkey: Optional[str] = None,
        timestamp=None,
    ):
        product = product if product is not None else self.default_product
        timestamp = timestamp or timezone.now()
        txn = AnalyticsTxn(product or self.default_product, pennkey, timestamp, data)
        self.submit_transaction(txn)


class AnalyticsRecorder(AnalyticsSubmitter):
    @staticmethod
    def _extract_explicit_args(explicit_arg_names, args, kwargs):
        from_args = args[: len(explicit_arg_names)]
        missing_explicit_args = explicit_arg_names[len(from_args) :]
        from_kwargs = tuple(kwargs[arg_name] for arg_name in missing_explicit_args)
        return from_args + from_kwargs

    @staticmethod
    def _compute_request_key_template(request):
        prefix = request.resolver_match.view_name.replace(":", ".").replace("-", "_")
        suffix = request.method.lower()
        return Template(f"{prefix}$name.{suffix}")

    """
    Creates a decorator that records analytics for an APIView (includes ViewSets)

    Sends all entries in the same transaction using key <app>.<view_name>.<name>.<method>
    and the request user's pennkey
    """

    def record_apiview(
        analytics_recorder,  # should be self but collides with self in WrappedClass
        *entries: ViewEntry,
    ) -> Callable[[Type[APIView]], Type[APIView]]:
        def decorator(cls):
            class WrappedClass(cls):
                def dispatch(self, *args, **kwargs):
                    before_contexts = AnalyticsEntry.compute_before_contexts(entries)

                    response = super().dispatch(*args, **kwargs)

                    accepted_entries = [
                        e
                        for e in entries
                        if e.accept_action(getattr(self, "action", None))
                        and e.accept_method(self.request.method)
                    ]

                    key_template = analytics_recorder._compute_request_key_template(
                        self.request
                    )

                    if data_list := AnalyticsEntry.compute_data_list(
                        key_template,
                        self.request,
                        response,
                        accepted_entries,
                        before_contexts,
                    ):
                        analytics_recorder.submit(
                            data_list,
                            pennkey=getattr(self.request.user, "username", None),
                        )
                    return response

            return WrappedClass

        return decorator

    """
    Creates a decorator that records analytics for a function in an APIView. Assumes
    the second argument is the request object.

    Sends all entries in the same transaction using key <app>.<view_name>.<name>.<method>
    and the request user's pennkey
    """

    def record_api_function(
        analytics_recorder, *entries: FuncEntry  # should be self but consitency
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        # assumes first arg is self and second arg is request
        def decorator(func):
            explicit_args_names = func.__code__.co_varnames[: func.__code__.co_argcount]

            @wraps(func)
            def wrapped_func(*args, **kwargs):
                explicit_args = analytics_recorder._extract_explicit_args(
                    explicit_args_names, args, kwargs
                )

                before_contexts = AnalyticsEntry.compute_before_contexts(entries)

                request = explicit_args[1]
                response = func(*args, **kwargs)

                key_template = AnalyticsRecorder._compute_request_key_template(request)

                if data_list := AnalyticsEntry.compute_data_list(
                    key_template, explicit_args, response, entries, before_contexts
                ):
                    analytics_recorder.submit(
                        data_list, pennkey=getattr(request.user, "username", None)
                    )

                return response

            return wrapped_func

        return decorator

    """
    Creates a decorator that records analytics for a function

    Sends all entries in the same transaction using key <module>.<function>.<name>
    and the pennkey returned by get_username.

    get_username: takes two arguments: the function's explicit arguments
    (up to *args or **kwargs) as a tuple and the function's return value

    See FuncEntry and UnaryFuncEntry for more information about which to use
    """

    def record_function(
        analytics_recorder,  # should be self but consitency
        *entries: FuncEntry | UnaryFuncEntry,
        get_username: Optional[Callable[[FunctionParam, FunctionReturn], Any]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func):
            # only explicit arguments (everything before *args or **kwargs)
            explicit_args_names = func.__code__.co_varnames[: func.__code__.co_argcount]

            unary_entries = [e for e in entries if isinstance(e, UnaryFuncEntry)]
            variadic_entries = [e for e in entries if isinstance(e, FuncEntry)]

            if len(unary_entries) > 0 and len(explicit_args_names) != 1:
                raise ValueError(
                    "UnaryFuncEntry can only be used with functions with a single argument"
                )

            @wraps(func)
            def wrapped_func(*args, **kwargs):
                explicit_args = analytics_recorder._extract_explicit_args(
                    explicit_args_names, args, kwargs
                )

                unary_before_contexts = AnalyticsEntry.compute_before_contexts(
                    unary_entries
                )
                variadic_before_contexts = AnalyticsEntry.compute_before_contexts(
                    variadic_entries
                )

                response = func(*args, **kwargs)

                key_template = Template(f"{func.__module__}.{func.__qualname__}$name")

                unary_data_list = (
                    AnalyticsEntry.compute_data_list(
                        key_template,
                        explicit_args[0],
                        response,
                        unary_entries,
                        unary_before_contexts,
                    )
                    if unary_entries
                    else []
                )

                variadic_data_list = AnalyticsEntry.compute_data_list(
                    key_template,
                    explicit_args,
                    response,
                    variadic_entries,
                    variadic_before_contexts,
                )

                if data_list := unary_data_list + variadic_data_list:
                    analytics_recorder.submit(
                        data_list,
                        pennkey=get_username and get_username(explicit_args, response),
                    )

                return response

            return wrapped_func

        return decorator


class LocalAnalyticsRecorder(AnalyticsRecorder):
    """
    Local analytics submitter for testing that simply prints the transaction
    """

    def submit_transaction(self, txn: AnalyticsTxn):
        print(
            colorize(f"Labs Analytics: Should be sending: {txn.to_json()}", fg="blue")
        )


class OffAnalyticsRecorder(AnalyticsRecorder):
    """
    Off analytics submitter that does nothing on submit
    """

    def submit_transaction(self, _txn: AnalyticsTxn):
        pass


class LabsAnalyticsRecorder(AnalyticsRecorder):
    """
    Python wrapper for async requests to Labs Analytics Engine
    """

    class NoRebuildAuthSession(Session):
        def rebuild_auth(self, prepared_request, response):
            """
            No code here means requests will always preserve the Authorization
            header when redirected.
            Be careful not to leak your credentials to untrusted hosts!
            """

    ANALYTICS_URL = "https://analytics.pennlabs.org/analytics"
    POOL_SIZE = 10

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(LabsAnalyticsRecorder, cls).__new__(cls)
        return cls.instance

    def __init__(self, default_product: Product):
        super().__init__(default_product)

        self.executor = ThreadPoolExecutor(max_workers=self.POOL_SIZE)
        self.session = LabsAnalyticsRecorder.NoRebuildAuthSession()

        self.expires_at = None
        self.headers = dict()

        # Local caching of expiration date and headers
        self._refresh_expires_at()
        self._refresh_headers()

    def _refresh_expires_at(self):
        self.expires_at = json.loads(container.access_jwt.claims)["exp"]

    def _refresh_headers(self):
        self.headers = {
            "Authorization": f"Bearer {container.access_jwt.serialize()}",
            "Content-Type": "application/json",
        }

    def submit_transaction(self, txn: AnalyticsTxn):
        try:
            # Offer a 30 second buffer to refresh
            # TODO: According to @judtinzhang, the reason we need this buffer is due to a
            # subtle bug on DLA with regards to tokens.
            if time.time() >= self.expires_at - 30:
                _refresh_if_outdated()
                self._refresh_expires_at()
                self._refresh_headers()

            self.executor.submit(self._send_message, txn.to_json())
        except Exception:
            # As to not interrupt everyday business logic products do when the analytics
            # server is down, we should not raise an exception.

            # TODO: However, we should be logging this error so that we can investigate.
            # We should set up a logging infrastructure to do this.
            pass

    def _send_message(self, json):
        self.session.post(url=self.ANALYTICS_URL, json=json, headers=self.headers)


def get_analytics_recorder(default_product: Product, off=False) -> AnalyticsRecorder:
    if off:
        return OffAnalyticsRecorder(default_product)
    try:
        return LabsAnalyticsRecorder(default_product)
    except Exception as e:
        print(colorize(f"Error initializing AnalyticsRecoder: {e}", fg="red"))
        print("Falling back to LocalAnalyticsSubmitter\n")
        return LocalAnalyticsRecorder(default_product)
