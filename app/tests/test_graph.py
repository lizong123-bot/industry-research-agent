# app/tests/test_graph.py
from app.deps import graph
from app.graph.state import make_initial_state
from langgraph.types import Command

def test_full_flow():
    config = {"configurable": {"thread_id": "test-1"}}

    print("=== 启动 ===")
    graph.invoke(make_initial_state("2026 AI Agent 市场规模"), config=config)
    snap = graph.get_state(config)
    print("暂停在：", snap.next)

    print("=== 恢复（流式） ===")
    for event in graph.stream(
        Command(resume=snap.values["outline"]),
        config=config,
        stream_mode="updates",
    ):
        for node_name, output in event.items():
            print(f"[节点] {node_name} -> {list(output.keys()) if output else '无更新'}")

    final = graph.get_state(config).values.get("final_report")
    print("=== 报告 ===")
    print(final if final else "(空)")