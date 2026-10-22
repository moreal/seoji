import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

SEOJI_URL = "https://www.nl.go.kr/seoji/SearchApi.do"
RETRY_DELAYS = (1.0, 2.0, 4.0)
FATAL_CODES = {"000", "010", "011", "012"}


class SeojiError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class PageSizeTooLarge(SeojiError):
    pass


class FatalSeojiError(SeojiError):
    pass


@dataclass
class SeojiPage:
    total_count: int
    page_no: int
    docs: list[dict[str, str]]
    raw: dict
    params: dict  # request parameters without cert_key


class SeojiClient:
    def __init__(
        self,
        cert_key: str,
        *,
        base_url: str = SEOJI_URL,
        http: httpx.Client | None = None,
        min_interval: float = 1.0,
        timeout: float = 10.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._cert_key = cert_key
        self._base_url = base_url
        self._http = http or httpx.Client(timeout=timeout)
        self._min_interval = min_interval
        self._sleep = sleep
        self._clock = clock
        self._last_call: float | None = None

    def _throttle(self) -> None:
        if self._last_call is not None:
            wait = self._min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def _get_json(self, params: dict) -> dict:
        """GET with retries. Errors never carry the URL, because it contains cert_key."""
        for attempt in range(len(RETRY_DELAYS) + 1):
            self._throttle()
            try:
                resp = self._http.get(self._base_url, params=params)
            except httpx.TransportError as e:
                error = SeojiError("network", type(e).__name__)
            else:
                if resp.status_code == 429 or resp.status_code >= 500:
                    error = SeojiError(f"http_{resp.status_code}", "server busy or failing")
                elif resp.status_code >= 400:
                    raise SeojiError(f"http_{resp.status_code}", "request rejected") from None
                else:
                    try:
                        return resp.json()
                    except ValueError:
                        error = SeojiError("bad_body", "response is not JSON")
            if attempt == len(RETRY_DELAYS):
                raise error from None
            self._sleep(RETRY_DELAYS[attempt])
        raise AssertionError("unreachable")

    def search(self, **params) -> SeojiPage:
        public = {k: str(v) for k, v in params.items()} | {"result_style": "json"}
        raw = self._get_json(public | {"cert_key": self._cert_key})
        if raw.get("RESULT") == "ERROR":
            code, message = str(raw.get("ERR_CODE", "")), str(raw.get("ERR_MESSAGE", ""))
            if code == "013":
                raise PageSizeTooLarge(code, message)
            if code in FATAL_CODES:
                raise FatalSeojiError(code, message)
            raise SeojiError(code, message)
        if "resultCode" in raw and "docs" not in raw:  # a second error envelope seen in practice
            raise SeojiError(str(raw["resultCode"]), str(raw.get("resultMsg", "")))
        return SeojiPage(
            total_count=int(raw.get("TOTAL_COUNT") or 0),
            page_no=int(raw.get("PAGE_NO") or public.get("page_no", 1)),
            docs=raw.get("docs") or [],
            raw=raw,
            params=public,
        )
