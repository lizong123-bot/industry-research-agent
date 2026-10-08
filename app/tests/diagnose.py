# app/tests/diagnose.py
from app.deps import graph
from app.graph.state import make_initial_state
from langgraph.types import Command

config = {"configurable": {"thread_id": "diag-2"}}

# === 启动 ===
graph.invoke(make_initial_state("2026 AI Agent 市场规模"), config=config)
snap = graph.get_state(config)

# === 恢复，流式看每轮 Reflect ===
round_num = 0
last_total = 0
for event in graph.stream(
    Command(resume=snap.values["outline"]),
    config=config,
    stream_mode="updates",
):
    for node_name, output in event.items():
        if node_name == "reflect":
            round_num += 1
            print(f"\n>>> 第 {round_num} 轮 Reflect 后:")
            for q in output.get("outline", []):
                print(f"  {q['id']}: missing={q['missing_sub_questions']}, "
                      f"failed={q['reflection_failed']}, count={q['search_result_count']}")
        elif node_name == "research":
            all_pages = output.get("web_pages", [])
            new_pages = all_pages[last_total:]
            last_total = len(all_pages)
            qids = [p["related_question_id"] for p in new_pages]
            print(f"\n[Research] 本轮新增 {len(new_pages)} 个，qid: {qids}")
        else:
            print(f"[{node_name}]")

# === 最终状态 ===
final_state = graph.get_state(config).values

print(final_state["final_report"])