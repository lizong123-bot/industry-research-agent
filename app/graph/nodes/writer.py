# app/graph/nodes/writer.py
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

from app.graph.state import State
from app.tools.llm import call_llm_text, LLMCallError

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "writer.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def writer_node(state: State) -> dict:
    """汇总证据，生成结构化报告。LLM 失败时降级为原始材料。"""
    outline = state["outline"]

    # 1. 组装按子问题分组的证据（带编号 + 域名）
    evidence_by_q: dict[str, list[dict]] = {}
    ref_list: list[str] = []
    for q in outline:
        items = []
        for p in state["web_pages"]:
            if p["related_question_id"] != q["id"]:
                continue
            idx = len(ref_list) + 1
            domain = urlparse(p["url"]).netloc or "unknown"
            ref_list.append(f"[{idx}] {p['title']} ({domain}) - {p['url']}")
            summary = p["summary"] if p["summary"] else "（摘要失败）"
            items.append({"ref": idx, "title": p["title"], "url": p["url"], "summary": summary})
        evidence_by_q[q["id"]] = items

    # 2. 组装标注列表（代码检测硬事实）
    annotations = []
    for q in outline:
        if q["reflection_failed"]:
            annotations.append(f"子问题 {q['id']}（{q['question']}）：反思环节失败，此部分判断不可靠")
        elif q["missing_sub_questions"]:
            annotations.append(f"子问题 {q['id']}（{q['question']}）：信息不足，缺 {q['missing_sub_questions']}")

    # 3. 组装 prompt
    outline_for_llm = [
        {"id": q["id"], "question": q["question"], "evidence": evidence_by_q[q["id"]]}
        for q in outline
    ]
    prompt = (
        _PROMPT_TEMPLATE
        .replace("{topic}", state["topic"])
        .replace("{outline}", json.dumps(outline_for_llm, ensure_ascii=False))
        .replace("{annotations}", json.dumps(annotations, ensure_ascii=False))
    )

    # 4. 调 LLM
    try:
        report = call_llm_text(prompt)
        final = f"{report}\n\n---\n\n## 参考来源\n\n" + "\n".join(ref_list)
        return {"final_report": final}
    except LLMCallError as e:
        logger.warning("writer LLM failed, fallback to raw: %s", e)

    # 5. 降级报告
    lines = [f"# {state['topic']}\n", "> LLM 摘要失败，以下是原始材料。\n"]
    for q in outline:
        lines.append(f"## {q['question']}\n")
        for item in evidence_by_q[q["id"]]:
            lines.append(f"- [{item['ref']}] {item['title']} — {item['url']}")
            lines.append(f"  {item['summary']}\n")
    if ref_list:
        lines.append("---\n\n## 参考来源\n")
        lines.extend(ref_list)
    return {"final_report": "\n".join(lines)}