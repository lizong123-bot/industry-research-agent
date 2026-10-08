# app/graph/nodes/research.py
import logging
from datetime import datetime, timezone

from app.graph.state import State, make_web_page
from app.storage.content_store import save_content
from app.tools.search import search, SearchError
from app.tools.scraper import scrape, ScrapeError

logger = logging.getLogger(__name__)

MAX_PAGES_PER_QUERY = 5


def research_node(state: State) -> dict:
    """搜 next_question_id 的 queries，抓网页，返回新增的 web_pages。"""
    qid = state["next_question_id"]
    sub_q = next(q for q in state["outline"] if q["id"] == qid)

    new_pages: list[dict] = []
    seen_urls: set[str] = set()
    request_count_total = 0

    for query in sub_q["missing_sub_questions"]:
        try:
            result = search(query)
        except SearchError as e:
            logger.warning("search failed for %r: %s", query, e)
            continue
        request_count_total += result.request_count

        for r in result.results[:MAX_PAGES_PER_QUERY]:
            url = r["link"]
            if url in seen_urls:
                continue
            seen_urls.add(url)

            try:
                content = scrape(url)
            except ScrapeError as e:
                logger.warning("scrape failed for %s: %s", url, e)
                continue

            content_ref = save_content(content)
            page = make_web_page(
                url=url,
                title=r.get("title", ""),
                content_ref=content_ref,
                related_question_id=qid,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
            new_pages.append(page)

    new_outline = [
        {**q, "search_result_count": q["search_result_count"] + len(new_pages)}
        if q["id"] == qid else q
        for q in state["outline"]
    ]
    return {
        "web_pages": state["web_pages"] + new_pages,
        "tool_call_count": state["tool_call_count"] + request_count_total,
        "outline": new_outline,
    }