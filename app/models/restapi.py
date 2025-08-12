"""
Class for generic REST API requests that uses an exponential retry loop.

"""
# For retry loop
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import requests

class RestAPI:

    def __init__(self):
        self.responsejson = ''
        self.url = ''
        self.error = None

    def getresponsejson(self, url: str) -> dict:
        """
        Obtains a response from a REST API.
        Employs a retry loop in case of timeout or other failures.

        :param url: the URL to the REST API
        :return: the response JSON
        """

        self.url = url

        # Use the HTTPAdapter's retry strategy, as described here:
        # https://oxylabs.io/blog/python-requests-retry

        # Five retries max.
        # A backoff factor of 2, which results in exponential increases in delays before each attempt.
        # Retry for scenarios such as Service Unavailable or Too Many Requests that often are returned in case
        # of an overloaded server.
        try:
            retry = Retry(
                total=5,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504]
            )

            adapter = HTTPAdapter(max_retries=retry)

            session = requests.Session()
            session.mount('https://', adapter)
            r = session.get(url=url, timeout=180)

            self.responsejson = r.json()
            self.error = None

            return self.responsejson

        except Exception as e:
            self.error = e
            r.raise_for_status()