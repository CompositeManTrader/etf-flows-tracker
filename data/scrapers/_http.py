"""Shared HTTP session with retries + realistic User-Agent.

GitHub Actions runners use AWS IPs that some CDNs (Cloudflare, Akamai)
treat as suspicious. A realistic UA + Accept headers reduces 403s.
"""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_DEFAULT_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_DEFAULT_HEADERS)
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def get_text(url: str, timeout: int = 20, **kwargs) -> str | None:
    try:
        with make_session() as s:
            r = s.get(url, timeout=timeout, **kwargs)
            if r.status_code != 200:
                return None
            return r.text
    except Exception:  # noqa: BLE001
        return None


def get_bytes(url: str, timeout: int = 30, **kwargs) -> bytes | None:
    try:
        with make_session() as s:
            r = s.get(url, timeout=timeout, **kwargs)
            if r.status_code != 200:
                return None
            return r.content
    except Exception:  # noqa: BLE001
        return None
