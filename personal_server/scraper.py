from __future__ import annotations

import html
import re
import urllib.request
from html.parser import HTMLParser
from typing import Tuple


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.chunks.append(text)

    def get_text(self) -> str:
        return "\n".join(self.chunks)


def fetch_url(url: str, timeout: int = 20) -> Tuple[str, str, str]:
    """Return (final_url, html, title)"""
    req = urllib.request.Request(url, headers={"User-Agent": "PersonalServer/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        html_bytes = resp.read()
        html_text = html_bytes.decode(charset, errors="replace")
        title = _extract_title(html_text)
        return str(resp.geturl()), html_text, title


def html_to_text(html_text: str) -> str:
    parser = _TextExtractor()
    parser.feed(html_text)
    return parser.get_text()


def _extract_title(html_text: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return html.unescape(m.group(1)).strip()

