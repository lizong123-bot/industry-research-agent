# app/tools/search.py
import time
import random
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from serpapi import GoogleSearch

from app.config import SERPAPI_KEY, SEARCH_MAX_RETRIES


class SearchError(Exception):
    """搜索失败（重试耗尽 / API 错误）。调用方必须显式处理。"""


@dataclass
class SearchResult:
    results: list[dict]        # [{"title", "link", "snippet"}]
    request_count: int         # 实际 HTTP 请求次数（用于成本统计）


_RETRYABLE = (requests.exceptions.Timeout, requests.exceptions.ConnectionError)

# 黑名单：明显无关的域名（应用商店、成人、购物、短视频、播客、纯推荐页等）
_BLOCKED_DOMAINS = {
    "apps.apple.com",
    "play.google.com",
    "lanrlanr.com",
    "castro.fm",
    "help.shopify.com",
    "mofcom.gov.cn",
    "yhsubian.com",
    "youtube.com",
    "bilibili.com",
    "douyin.com",
    "taobao.com",
    "jd.com",
}


def _is_blocked(url: str) -> bool:
    """判断 URL 是否属于黑名单域名。"""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return True
    domain = domain.removeprefix("www.")
    return any(domain == bd or domain.endswith("." + bd) for bd in _BLOCKED_DOMAINS)


def search(query: str) -> SearchResult:
    """
    搜一个 query，返回裁剪后的结果 + 实际请求次数。
    - 搜不到 → SearchResult([], n)
    - 重试耗尽 / API 错误 → raise SearchError
    """
    request_count = 0
    last_exc = None

    for attempt in range(SEARCH_MAX_RETRIES):
        request_count += 1                 # 请求前累加：发出即计费
        try:
            raw = _do_search(query)
        except _RETRYABLE as e:
            last_exc = e
            if attempt == SEARCH_MAX_RETRIES - 1:
                break
            delay = min(2 ** attempt + random.uniform(0, 1), 30)
            time.sleep(delay)
            continue

        # API 业务错误：HTTP 非 200 但不抛，藏在 error 字段
        if "error" in raw:
            raise SearchError(f"SerpAPI error: {raw['error']}")

        # 裁剪字段 + 过滤黑名单域名
        raw_results = raw.get("organic_results", [])
        results = []
        for r in raw_results:
            link = r.get("link", "")
            if not link or _is_blocked(link):
                continue
            results.append({
                "title": r.get("title", ""),
                "link": link,
                "snippet": r.get("snippet", ""),
            })
        return SearchResult(results=results, request_count=request_count)

    raise SearchError(
        f"Search failed after {SEARCH_MAX_RETRIES} attempts: {last_exc}"
    )


def _do_search(query: str) -> dict:
    return GoogleSearch({
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "q": query,
    }).get_dict()