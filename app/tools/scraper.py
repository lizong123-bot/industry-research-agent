# app/tools/scraper.py
import requests
import trafilatura

from app.config import SCRAPE_TIMEOUT


class ScrapeError(Exception):
    """网页抓取/正文提取失败。调用方必须显式处理。"""


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape(url: str) -> str:
    """抓取网页正文纯文本。失败 → raise ScrapeError。"""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=SCRAPE_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ScrapeError(f"Fetch failed: {url} ({type(e).__name__})") from e

    text = trafilatura.extract(
        resp.text,
        include_comments=False,
        include_tables=True,
        favor_precision=False,
    )

    if not text:
        raise ScrapeError(f"Extraction returned empty: {url}")

    return text