from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class AllplanHostError(RuntimeError):
    """Raised when the local Allplan Python host cannot handle a request."""


class AllplanHostClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

    def post(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload or {}).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        request = Request(
            urljoin(self.base_url, path.lstrip("/")),
            data=body,
            headers=request_headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise AllplanHostError(
                f"Allplan host returned HTTP {exc.code} for {path}: {error_body}"
            ) from exc
        except URLError as exc:
            raise AllplanHostError(
                "Could not reach the Allplan host. Start the StartPythonHost "
                f"PythonPart and verify ALLPLAN_HOST_URL={self.base_url.rstrip('/')}."
            ) from exc

        if not raw_body:
            return {}

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise AllplanHostError(
                f"Allplan host returned invalid JSON for {path}: {raw_body}"
            ) from exc

        if not isinstance(data, dict):
            raise AllplanHostError(
                f"Allplan host returned a non-object response for {path}: {data!r}"
            )

        return data
