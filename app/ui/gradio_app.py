# app/ui/gradio_app.py
import json

import gradio as gr
import requests

API = "http://127.0.0.1:8000"


def start_research(topic: str):
    """启动调研，返回 (thread_id, outline_json, status)。"""
    if not topic.strip():
        return "", "", "⚠️ 请输入调研主题"

    try:
        r = requests.post(f"{API}/research", json={"topic": topic}, timeout=30)
        r.raise_for_status()
    except Exception as e:
        return "", "", f"❌ 启动失败: {e}"

    thread_id = r.json()["thread_id"]

    try:
        r = requests.get(f"{API}/research/{thread_id}", timeout=30)
        r.raise_for_status()
    except Exception as e:
        return thread_id, "", f"❌ 查询状态失败: {e}"

    data = r.json()
    outline_json = json.dumps(data.get("outline") or [], ensure_ascii=False, indent=2)
    return thread_id, outline_json, f"⏸️ {data.get('status', 'unknown')}"


def resume_research(thread_id: str, outline_json: str):
    """提交提纲并启动后台调研，立即返回。"""
    if not thread_id:
        return "⚠️ 请先点击『启动』"
    if not outline_json.strip():
        return "⚠️ 提纲不能为空"

    try:
        outline = json.loads(outline_json)
    except json.JSONDecodeError as e:
        return f"❌ 提纲 JSON 格式错误: {e}"

    if not isinstance(outline, list):
        return "❌ 提纲必须是数组（list）"

    try:
        r = requests.post(
            f"{API}/research/{thread_id}/resume",
            json={"outline": outline},
            timeout=30,
        )
        r.raise_for_status()
    except Exception as e:
        return f"❌ 恢复失败: {e}"

    return "🚀 已启动后台调研。请稍后点『🔄 刷新状态』查看进度。"


def refresh_status(thread_id: str):
    """刷新状态；如果 done，返回报告。"""
    if not thread_id:
        return "⚠️ 请先启动调研", ""

    try:
        r = requests.get(f"{API}/research/{thread_id}", timeout=30)
        r.raise_for_status()
    except Exception as e:
        return f"❌ 查询失败: {e}", ""

    data = r.json()
    status = data.get("status")
    report = data.get("final_report") or ""

    if status == "done":
        return "✅ 完成", report or "（报告为空）"
    if status == "running":
        return "⏳ 后台调研进行中……", report
    if status == "waiting_for_review":
        return "⏸️ 等待人工审阅", report

    return f"状态: {status}", report


with gr.Blocks(title="行业调研 Agent") as demo:
    gr.Markdown("# 🔍 行业调研 Agent")
    gr.Markdown("输入主题 → 启动 → 审阅/修改提纲 → 确认 → **点『🔄 刷新状态』查看进度**")

    thread_id_state = gr.State("")

    with gr.Row():
        topic_input = gr.Textbox(
            label="调研主题",
            placeholder="例如：2026 AI Agent 市场规模",
            scale=4,
        )
        start_btn = gr.Button("🚀 启动", scale=1)

    status_output = gr.Textbox(label="状态", interactive=False)

    outline_input = gr.Code(
        label="提纲（可编辑 JSON）—— 修改后点『确认并继续』",
        language="json",
        lines=18,
    )

    with gr.Row():
        resume_btn = gr.Button("✅ 确认并继续", variant="primary", scale=2)
        refresh_btn = gr.Button("🔄 刷新状态", scale=1)

    report_output = gr.Markdown(label="报告")

    start_btn.click(
        fn=start_research,
        inputs=[topic_input],
        outputs=[thread_id_state, outline_input, status_output],
    )
    resume_btn.click(
        fn=resume_research,
        inputs=[thread_id_state, outline_input],
        outputs=[status_output],
    )
    refresh_btn.click(
        fn=refresh_status,
        inputs=[thread_id_state],
        outputs=[status_output, report_output],
    )


if __name__ == "__main__":
    demo.launch(server_port=7860)