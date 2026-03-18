"""
Prompt 守护 Agent（A5）

输入:
  conversation_summary: str  - 本次对话的要点摘要

输出:
  need_update: bool          - 是否建议更新 prompt
  diff_display: str          - 供展示给用户的 diff 说明（Markdown）
  suggestions: list          - 原子操作建议列表
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROMPTS_DIR, make_llm


class GuardianState(TypedDict):
    conversation_summary: str
    current_prompt: str
    suggestions: Optional[List[dict]]
    diff_display: Optional[str]
    need_update: bool
    input_tokens: int
    output_tokens: int


def analyze_node(state: GuardianState) -> GuardianState:
    system_prompt = (PROMPTS_DIR / "prompt_guardian.md").read_text(encoding="utf-8")
    llm = make_llm()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=(
                f"当前系统提示词：\n\n{state['current_prompt']}\n\n"
                f"本次对话摘要：\n\n{state['conversation_summary']}\n\n"
                "请分析是否需要更新，并按要求输出 JSON。"
            )
        ),
    ]

    response = llm.invoke(messages)

    # 收集 token 使用情况
    usage = response.response_metadata.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    try:
        # 提取 JSON（兼容模型在 JSON 前后输出少量文字的情况）
        text = response.content.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        result = json.loads(text[start:end])
    except Exception:
        result = {"need_update": False, "reason": "响应解析失败，保守处理为无需更新", "suggestions": []}

    suggestions = result.get("suggestions", [])
    need_update = result.get("need_update", False) and len(suggestions) > 0

    if need_update:
        diff_lines = ["## Prompt 更新建议\n", "> 以下每条建议为一个原子操作，需逐条确认。\n"]
        for i, s in enumerate(suggestions, 1):
            action_label = {"add": "追加", "delete": "删除", "modify": "修改"}.get(s.get("action"), s.get("action"))
            diff_lines.append(f"### 建议 {i}：{action_label}")
            diff_lines.append(f"**位置**：{s.get('location', '未指定')}")
            if s.get("original"):
                diff_lines.append(f"```\n- {s['original']}\n```")
            if s.get("new"):
                diff_lines.append(f"```\n+ {s['new']}\n```")
            diff_lines.append(f"**原因**：{s.get('reason', '')}\n")
        diff_display = "\n".join(diff_lines)
    else:
        diff_display = f"**无需更新**\n\n原因：{result.get('reason', '本次对话未发现需要调整系统提示词的场景')}"

    return {
        **state,
        "suggestions": suggestions,
        "diff_display": diff_display,
        "need_update": need_update,
        "input_tokens": state.get("input_tokens", 0) + input_tokens,
        "output_tokens": state.get("output_tokens", 0) + output_tokens,
    }


def build_graph():
    graph = StateGraph(GuardianState)
    graph.add_node("analyze", analyze_node)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", END)
    return graph.compile()


_app = None


def _get_app():
    global _app
    if _app is None:
        _app = build_graph()
    return _app


def run(input_data: dict) -> dict:
    current_prompt = (PROMPTS_DIR / "system_designer.md").read_text(encoding="utf-8")
    app = _get_app()
    result = app.invoke({
        "conversation_summary": input_data.get("conversation_summary", ""),
        "current_prompt": current_prompt,
        "suggestions": None,
        "diff_display": None,
        "need_update": False,
        "input_tokens": 0,
        "output_tokens": 0,
    })
    return {
        "need_update": result["need_update"],
        "diff_display": result["diff_display"],
        "suggestions": result.get("suggestions", []),
        "usage": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        }
    }
