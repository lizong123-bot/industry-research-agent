from pydantic import BaseModel


# ---------- Planner ----------
class PlannerQuestion(BaseModel):
    question: str

class PlannerOutput(BaseModel):
    questions: list[PlannerQuestion]


# ---------- Reflect ----------
class ReflectOutput(BaseModel):
    missing: list[str]                  # 待补充的可搜索 query；空 = 够了
    next_question_id: str | None        # 下一轮搜谁；None = 没有未完成的