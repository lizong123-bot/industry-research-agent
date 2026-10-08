# app/graph/nodes/human_review.py
from langgraph.types import interrupt

from app.graph.state import State


def human_review_node(state: State) -> dict:
    """暂停等人审阅/修改提纲。无副作用（不调 LLM），可被 resume 重跑。"""
    outline = state["outline"]

    if not outline:
        message = "提纲为空，请补充"
    else:
        message = "请审阅并修改提纲，确认后继续"

    revised_outline = interrupt({"outline": outline, "message": message})
    return {"outline": revised_outline or outline}