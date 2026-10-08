# app/graph/builder.py
from langgraph.graph import StateGraph, START, END

from app.graph.state import State
from app.graph.edges import should_continue
from app.graph.nodes.planner import planner_node
from app.graph.nodes.human_review import human_review_node
from app.graph.nodes.init_pointer import init_research_pointer_node
from app.graph.nodes.research import research_node
from app.graph.nodes.summarize import summarize_node
from app.graph.nodes.reflect import reflect_node
from app.graph.nodes.writer import writer_node


def build_graph(checkpointer=None):
    graph = StateGraph(State)

    # 节点
    graph.add_node("planner", planner_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("init", init_research_pointer_node)
    graph.add_node("research", research_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("writer", writer_node)

    # 普通边
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "human_review")
    graph.add_edge("human_review", "init")
    graph.add_edge("init", "research")
    graph.add_edge("research", "summarize")
    graph.add_edge("summarize", "reflect")
    graph.add_edge("writer", END)

    # 条件边
    graph.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "research": "research",
            "writer": "writer",
            "reinit": "init",
        },
    )

    return graph.compile(checkpointer=checkpointer)