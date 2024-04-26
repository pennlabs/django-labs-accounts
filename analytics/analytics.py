import json
import time
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from typing import Optional

from django.utils import timezone
from requests import Session

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
        timestamp=timezone.now(),
        data=list(),
    ):
        self.product = product.value
        self.pennkey = pennkey
        self.timestamp = timestamp.timestamp()
        self.data = data

    def to_json(self):
        return json.loads(json.dumps(vars(self)))


class NoRebuildAuthSession(Session):
    def rebuild_auth(self, prepared_request, response):
        """
        No code here means requests will always preserve the Authorization
        header when redirected.
        Be careful not to leak your credentials to untrusted hosts!
        """


class LabsAnalytics:
    """
    Python wrapper for async requests to Labs Analytics Engine
    """

    ANALYTICS_URL = "https://analytics.pennlabs.org/analytics"
    POOL_SIZE = 10

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(LabsAnalytics, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=self.POOL_SIZE)
        self.session = NoRebuildAuthSession()

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

    def submit(self, txn: AnalyticsTxn):
        # Offer a 30 second buffer to refresh
        if time.time() >= self.expires_at - 30:
            _refresh_if_outdated()
            self._refresh_expires_at()
            self._refresh_headers()

        self.executor.submit(self.send_message, txn.to_json())

    def send_message(self, json):
        self.session.post(url=self.ANALYTICS_URL, json=json, headers=self.headers)
