import json
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional

import requests
from django.utils import timezone


class Product(Enum):
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
        data=dict(),
    ):
        self.product = str(product)
        self.pennkey = pennkey
        self.timestamp = timestamp.timestamp()
        self.data = data

    def to_json(self):
        return json.dumps(vars(self))


class LabsAnalytics:
    """
    Python wrapper for async requests to Labs Analytics Engine
    """

    ANALYTICS_URL = "https://jsonplaceholder.typicode.com/posts"
    POOL_SIZE = 10

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(LabsAnalytics, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=self.POOL_SIZE)

    def submit(self, txn: AnalyticsTxn):
        headers = {}
        self.executor.submit(self.request_job, txn.to_json(), headers)

    def request_job(self, json, headers):
        requests.post(self.ANALYTICS_URL, json=json, headers=headers)
