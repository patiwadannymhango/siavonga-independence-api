import requests
from django.conf import settings


class LipilaAPIError(Exception):
    """Raised when Lipila returns an API error."""


class LipilaClient:
    def __init__(self):
        if settings.LIPILA_ENVIRONMENT == "production":
            self.base_url = settings.LIPILA_PRODUCTION_BASE_URL
            self.api_key = settings.LIPILA_PRODUCTION_API_KEY
        else:
            self.base_url = settings.LIPILA_SANDBOX_BASE_URL
            self.api_key = settings.LIPILA_SANDBOX_API_KEY

    @property
    def headers(self):
        return {"accept": "application/json", "x-api-key": self.api_key}

    def request(self, method, endpoint, *, data=None, params=None, callback_url=None):
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        headers = self.headers.copy()

        # Some Lipila endpoints reject a Content-Type: application/json
        # header on requests with no body — only send it when there
        # actually is one.
        if data is not None:
            headers["Content-Type"] = "application/json"

        if callback_url:
            headers["callbackUrl"] = callback_url

        response = requests.request(method=method, url=url, headers=headers, json=data, params=params, timeout=30)

        try:
            response_data = response.json()
        except ValueError:
            response_data = {"raw_response": response.text}

        if not response.ok:
            raise LipilaAPIError(response_data)

        return response_data
