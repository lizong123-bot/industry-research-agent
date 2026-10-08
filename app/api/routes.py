# app/api/routes.py
import uuid

from fastapi import APIRouter, BackgroundTasks
from langgraph.types import Command

from app.api.schemas import (
    ResearchRequest, ResearchStartResponse,
    ResumeRequest, StatusResponse,
)
from app.deps import graph
from app.graph.state import make_initial_state

router = APIRouter()


@router.post("/research", response_model=ResearchStartResponse)
def start_research(req: ResearchRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke(make_initial_state(req.topic), config=config)
    return ResearchStartResponse(thread_id=thread_id, status="waiting_for_review")


@router.get("/research/{thread_id}", response_model=StatusResponse)
def get_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)

    if not snapshot.next:
        return StatusResponse(
            status="done",
            outline=snapshot.values.get("outline"),
            final_report=snapshot.values.get("final_report"),
        )
    if snapshot.next == ("human_review",):
        return StatusResponse(
            status="waiting_for_review",
            outline=snapshot.values.get("outline"),
        )
    return StatusResponse(status="running", outline=snapshot.values.get("outline"))


@router.post("/research/{thread_id}/resume", response_model=StatusResponse)
def resume_research(thread_id: str, req: ResumeRequest, bg: BackgroundTasks):
    config = {"configurable": {"thread_id": thread_id}}

    def run():
        graph.invoke(Command(resume=req.outline), config=config)

    bg.add_task(run)
    return StatusResponse(status="running")