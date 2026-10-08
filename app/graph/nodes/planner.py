from pathlib import Path

from app.graph.schemas import PlannerOutput
from app.graph.state import State, make_sub_question
from app.tools.llm import call_llm_json


_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "planner.txt"


def planner_node(state: State) -> dict:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.replace("{topic}", state["topic"])

    result = call_llm_json(prompt, PlannerOutput)

    outline = [
        make_sub_question(f"q{i + 1}", q.question)
        for i, q in enumerate(result.questions)
    ]
    return {"outline": outline}