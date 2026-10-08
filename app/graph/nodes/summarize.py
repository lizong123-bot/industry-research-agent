# app/graph/nodes/summarize.py
import logging
from pathlib import Path

from app.graph.state import State
from app.storage.content_store import load_content
from app.tools.llm import call_llm_text, LLMCallError

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "summarize.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")
_MAX_CONTENT_CHARS = 8000


def summarize_node(state: State) -> dict:
    """给未摘要的网页生成摘要。返回更新后的 web_pages。"""
    updated = []

    for page in state["web_pages"]:
        if page["summarized"]:
            updated.append(page)
            continue

        # 1. 加载正文
        try:
            content = load_content(page["content_ref"])
        except FileNotFoundError as e:
            logger.warning("content missing for %s: %s", page["url"], e)
            updated.append({**page, "summarized": True, "summary_failed": True})
            continue

        # 2. 截断（仅当超长时加提示）
        if len(content) > _MAX_CONTENT_CHARS:
            truncated = content[:_MAX_CONTENT_CHARS] + "...(截断)"
        else:
            truncated = content

        # 3. 组装 prompt
        prompt = (
            _PROMPT_TEMPLATE
            .replace("{title}", page["title"])
            .replace("{content}", truncated)
        )

        # 4. 调 LLM
        try:
            summary = call_llm_text(prompt)
        except LLMCallError as e:
            logger.warning("summarize failed for %s: %s", page["url"], e)
            updated.append({**page, "summarized": True, "summary_failed": True})
            continue

        # 5. 成功
        updated.append({**page, "summary": summary, "summarized": True})

    return {"web_pages": updated}
