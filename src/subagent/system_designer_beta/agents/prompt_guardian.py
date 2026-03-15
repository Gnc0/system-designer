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
import os
import sys
from pathlib import Path
from typing import List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from config import PROMPTS_DIR, SKILL_ROOT

# 从 prompts 目录读取 Guardian 系统提示词
GUARDIAN_SYSTEM = (SKILL_ROOT / "prompts" / "prompt_guardian.md").read_text(encoding="utf-8")


class GuardianState(TypedDict):
    conversation_summary: str
    current_prompt: str
    suggestions: Optional[List[dict]]
    diff_display: Optional[str]
    need_update: bool


def analyze_node(state: GuardianState) -> GuardianState:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    messages = [
        SystemMessage(content=GUARDIAN_SYSTEM),
        HumanMessage(
            content=(
                f"当前系统提示词：\n\n{state['current_prompt']}\n\n"
                f"本次对话摘要：\n\n{state['conversation_summary']}\n\n"
                "请分析是否需要更新，并按要求输出 JSON。"
            )
        ),
    ]

    response = llm.invoke(messages)

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
    }


def build_graph():
    graph = StateGraph(GuardianState)
    graph.add_node("analyze", analyze_node)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", END)
    return graph.compile()


def run(input_data: dict) -> dict:
    current_prompt = (PROMPTS_DIR / "system_designer.md").read_text(encoding="utf-8")
    app = build_graph()
    result = app.invoke({
        "conversation_summary": input_data.get("conversation_summary", ""),
        "current_prompt": current_prompt,
        "suggestions": None,
        "diff_display": None,
        "need_update": False,
    })
    return {
        "need_update": result["need_update"],
        "diff_display": result["diff_display"],
        "suggestions": result.get("suggestions", []),
    }
