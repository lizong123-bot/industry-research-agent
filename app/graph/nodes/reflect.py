# app/graph/nodes/reflect.py
import json
import logging
from pathlib import Path

from app.config import MAX_ITERATIONS
from app.graph.schemas import ReflectOutput
from app.graph.state import State
from app.tools.llm import call_llm_json, LLMCallError

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "reflect.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def reflect_node(state: State) -> dict:
    """LLM 判定当前子问题是否够，更新 outline 和 next_question_id。"""
    qid = state["next_question_id"]
    outline = state["outline"]
    current = next(q for q in outline if q["id"] == qid)

    # 组装 outline（精简字段，只给 LLM 需要的）
    outline_for_llm = [
        {"id": q["id"], "question": q["question"], "missing": q["missing_sub_questions"]}
        for q in outline
    ]

    # 组装 evidence（当前子问题的，title + summary + url）
    evidence = [
        {"title": p["title"], "summary": p["summary"], "url": p["url"]}
        for p in state["web_pages"]
        if p["related_question_id"] == qid
    ]

    prompt = (
        _PROMPT_TEMPLATE
        .replace("{outline}", json.dumps(outline_for_llm, ensure_ascii=False))
        .replace("{current_question}", current["question"])
        .replace("{evidence}", json.dumps(evidence, ensure_ascii=False))
        .replace("{iteration}", str(state["iteration_count"] + 1))
        .replace("{max_iterations}", str(MAX_ITERATIONS))
        .replace("{evidence_count}", str(len(evidence)))
    )

    # ---- LLM 失败路径 ----
    try:
        result = call_llm_json(prompt, ReflectOutput)
    except LLMCallError:
        logger.warning("reflect LLM failed for %s", qid)
        new_outline = [
            {**q, "reflection_failed": True} if q["id"] == qid else q
            for q in outline
        ]
        next_qid = next(
            (q["id"] for q in new_outline
             if q["missing_sub_questions"] and not q["reflection_failed"]),
            None,
        )
        return {
            "outline": new_outline,
            "next_question_id": next_qid,
            "iteration_count": state["iteration_count"] + 1,
        }

    # ---- LLM 成功路径 ----
    cleaned_missing = [m.strip() for m in result.missing if m.strip()]

    # === 防打转兜底：新 missing 与上轮完全一致且已有证据 → 强制接受现状 ===
    previous_missing = current["missing_sub_questions"]
    if (
        cleaned_missing
        and set(cleaned_missing) == set(previous_missing)
        and current["search_result_count"] > 0
    ):


        cleaned_missing = []

    new_outline = [
        {**q, "missing_sub_questions": cleaned_missing} if q["id"] == qid else q
        for q in outline
    ]

    # 校验 LLM 给的 next_question_id；无效则兜底
    valid_ids = {q["id"] for q in new_outline}
    if result.next_question_id in valid_ids:
        next_qid = result.next_question_id
    else:
        next_qid = next(
            (q["id"] for q in new_outline
             if q["missing_sub_questions"] and not q["reflection_failed"]),
            None,
        )

    return {
        "outline": new_outline,
        "next_question_id": next_qid,
        "iteration_count": state["iteration_count"] + 1,
    }