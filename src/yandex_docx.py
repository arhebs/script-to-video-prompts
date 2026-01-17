from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import IO, cast
from urllib.parse import urlencode

_YANDEX_PUBLIC_DOWNLOAD_ENDPOINT = (
    "https://cloud-api.yandex.net/v1/disk/public/resources/download"
)


def resolve_public_download_href(public_url: str) -> str:
    url = f"{_YANDEX_PUBLIC_DOWNLOAD_ENDPOINT}?{urlencode({'public_key': public_url})}"
    with cast(IO[bytes], urllib.request.urlopen(url, timeout=60)) as resp:
        raw_bytes = resp.read()

    raw = raw_bytes.decode("utf-8")
    payload_obj = cast(object, json.loads(raw))
    if not isinstance(payload_obj, dict):
        raise ValueError("Yandex response must be a JSON object")

    payload = cast(dict[str, object], payload_obj)
    href_obj = payload.get("href")
    if not isinstance(href_obj, str) or not href_obj:
        raise ValueError("Yandex response missing 'href'")
    return href_obj


def download_public_file(public_url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    href = resolve_public_download_href(public_url)
    with cast(IO[bytes], urllib.request.urlopen(href, timeout=60)) as resp:
        data = resp.read()

    _ = dest.write_bytes(data)
