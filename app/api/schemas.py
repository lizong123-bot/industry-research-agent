# app/api/schemas.py
from pydantic import BaseModel


class ResearchRequest(BaseModel):
    topic: str


class ResearchStartResponse(BaseModel):
    thread_id: str
    status: str


class ResumeRequest(BaseModel):
    outline: list[dict]      # 人类修改后的 outline（SubQuestion 列表）


class StatusResponse(BaseModel):
    status: str              # "waiting_for_review" | "running" | "done"
    outline: list[dict] | None = None
    final_report: str | None = None