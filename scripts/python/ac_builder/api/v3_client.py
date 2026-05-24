"""ActiveCampaign REST API client.

Reads AC_API_URL and AC_API_KEY from environment (loaded from .env if present).
The /api/3 path is appended automatically.

Usage:
    from ac_builder import ACClient
    client = ACClient()
    response = client.get("users/me")
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ACAPIError(Exception):
    """Raised when ActiveCampaign returns a non-2xx response.

    Attributes:
        status_code: The HTTP status code.
        body: The response body, parsed as JSON if possible, otherwise raw text.
        url: The full request URL that errored.
    """

    def __init__(self, status_code: int, body: dict[str, Any] | str, url: str) -> None:
        self.status_code = status_code
        self.body = body
        self.url = url
        super().__init__(f"AC API error {status_code} on {url}: {body}")


class ACClient:
    """Thin wrapper around the ActiveCampaign REST API v3.

    Authenticates via the Api-Token header. Pulls credentials from env vars
    AC_API_URL and AC_API_KEY (loaded from .env if present).

    Example:
        >>> client = ACClient()
        >>> response = client.get("campaigns", params={"limit": 5})
        >>> print(response["campaigns"])
    """

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        from ac_builder.config import load_credentials

        creds = load_credentials()
        raw_url = (api_url or creds.get("AC_API_URL", "")).rstrip("/")
        self.api_key = api_key or creds.get("AC_API_KEY", "")

        if not raw_url:
            raise ValueError(
                "AC_API_URL not set. Run /ac-builder:verifying-setup or set in "
                "~/.config/ac-builder/config.env, ./ac-builder.env, or process env."
            )
        if not self.api_key:
            raise ValueError(
                "AC_API_KEY not set. Run /ac-builder:verifying-setup or set in "
                "~/.config/ac-builder/config.env, ./ac-builder.env, or process env."
            )

        # Normalise: ensure /api/3 suffix
        if raw_url.endswith("/api/3"):
            self.api_url = raw_url
        else:
            self.api_url = f"{raw_url}/api/3"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Api-Token": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        path = path.lstrip("/")
        url = f"{self.api_url}/{path}"
        logger.debug("%s %s kwargs=%s", method, url, {k: v for k, v in kwargs.items() if k != "json"})

        response = self.session.request(method, url, **kwargs)

        try:
            body: dict[str, Any] | str = response.json()
        except ValueError:
            body = response.text

        if not response.ok:
            raise ACAPIError(response.status_code, body, url)

        # The 204 No Content responses (e.g., DELETE) come back empty
        if not isinstance(body, dict):
            return {"raw": body}
        return body

    # Verb-specific helpers -------------------------------------------------

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", path, json=json)

    def put(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("PUT", path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("PATCH", path, json=json)

    def delete(self, path: str) -> dict[str, Any]:
        return self._request("DELETE", path)

    # Pagination ------------------------------------------------------------

    def paginate(
        self,
        path: str,
        key: str,
        limit: int = 100,
        params: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterate through every item in a paginated list endpoint.

        AC paginates with limit/offset; max limit is 100. This walks every page
        until an empty page or a partial page is returned.

        Args:
            path: API path (e.g., "campaigns")
            key: JSON key in the response that holds the list (e.g., "campaigns")
            limit: Page size, max 100
            params: Additional query parameters

        Yields:
            Each item from every page in order.
        """
        offset = 0
        base_params = dict(params or {})

        while True:
            page_params = {**base_params, "limit": limit, "offset": offset}
            response = self.get(path, params=page_params)

            items = response.get(key, [])
            if not items:
                break

            yield from items

            # If we got fewer than the page size, that's the last page
            if len(items) < limit:
                break

            offset += limit
