from concurrent.futures import ThreadPoolExecutor

import requests


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

    def submit(self, json):
        headers = {}
        self.executor.submit(self.request_job, json, headers)

    def request_job(self, json, headers):
        requests.post(self.ANALYTICS_URL, json=json, headers=headers)
