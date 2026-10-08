# app/graph/state.py
from typing import TypedDict

class SubQuestion(TypedDict):
    id: str
    question: str
    missing_sub_questions: list[str]   # 初始 [question]; 够→[]; 不够→覆盖
    search_result_count: int
    reflection_failed: bool


class WebPage(TypedDict):
    url: str
    title: str
    summary: str          # 初始 ""，summarize 节点填充
    content_ref: str      # 正文外部存储引用
    related_question_id: str
    summarized: bool      # 初始 False
    fetched_at: str
    summary_failed: bool


class State(TypedDict):
    topic: str
    outline: list[SubQuestion]  # 整体替换（默认）
    web_pages: list[WebPage]
    next_question_id: str | None
    tool_call_count: int
    iteration_count: int
    final_report: str


# ---------- 构造函数（弥补 TypedDict 不校验、无默认值的软肋） ----------

def make_sub_question(qid: str, question: str) -> SubQuestion:
    return {
        "id": qid,
        "question": question,
        "missing_sub_questions": [question],
        "search_result_count": 0,
        "reflection_failed": False,
    }


def make_web_page(
    url: str,
    title: str,
    content_ref: str,
    related_question_id: str,
    fetched_at: str,
) -> WebPage:
    return {
        "url": url,
        "title": title,
        "summary": "",
        "content_ref": content_ref,
        "related_question_id": related_question_id,
        "summarized": False,
        "summary_failed": False,
        "fetched_at": fetched_at,
    }


def make_initial_state(topic: str) -> State:
    return {
        "topic": topic,
        "outline": [],
        "web_pages": [],
        "next_question_id": None,
        "tool_call_count": 0,
        "iteration_count": 0,
        "final_report": "",
    }