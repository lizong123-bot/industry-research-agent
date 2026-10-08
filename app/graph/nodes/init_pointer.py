# app/graph/nodes/init_pointer.py
from app.graph.state import State


def init_research_pointer_node(state: State) -> dict:
    for q in state["outline"]:
        if q["missing_sub_questions"] and not q["reflection_failed"]:
            return {"next_question_id": q["id"]}
    return {"next_question_id": None}