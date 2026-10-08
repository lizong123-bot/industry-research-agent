# app/graph/edges.py
from app.config import MAX_ITERATIONS, MAX_TOOL_CALLS
from app.graph.state import State


def should_continue(state: State) -> str:
    """
    路由函数（条件边）。Reflect 之后调用，决定下一步。
    纯函数：只读 State，不调 LLM，不改 State。
    返回: "research" | "writer" | "reinit"
    """
    outline = state["outline"]

    all_done = all(
        len(q["missing_sub_questions"]) == 0 or q["reflection_failed"]
        for q in outline
    )

    if all_done:
        return "writer"

    # 判断 2：撞上限 → 软停（Writer 会读 missing 非空来标注）
    hit_limit = (
        state["iteration_count"] >= MAX_ITERATIONS
        or state["tool_call_count"] >= MAX_TOOL_CALLS
    )
    if hit_limit:
        return "writer"

    # 判断 3：还有未完成，但 Reflect 没指定 next → 兜底重定向
    if state["next_question_id"] is None:
        return "reinit"

    # 正常继续
    return "research"