"""
需求拆解 Agent（A2）

输入:
  image_path: str        - 图片文件路径（相对于 skill root 或绝对路径）
  user_description: str  - 用户补充说明（可为空字符串）

输出:
  draft: str             - 需求 Draft（Markdown 格式）
"""

import base64
import os
import sys
from pathlib import Path
from typing import Optional, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from config import PROMPTS_DIR, SKILL_ROOT


class RequirementsState(TypedDict):
    image_path: str
    user_description: str
    draft: Optional[str]


def analyze_image(state: RequirementsState) -> RequirementsState:
    system_prompt = (PROMPTS_DIR / "requirements_analyzer.md").read_text(encoding="utf-8")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    content = []

    # 解析图片路径（支持相对路径和绝对路径），为空则跳过图片
    raw_path = state.get("image_path", "").strip()
    if raw_path:
        image_path = Path(raw_path)
        if not image_path.is_absolute():
            image_path = SKILL_ROOT / image_path
        if not image_path.exists():
            return {**state, "draft": f"错误：图片文件不存在 - {image_path}"}

        # 读取图片并编码为 base64
        image_bytes = image_path.read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        suffix = image_path.suffix.lower()
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(suffix, "image/png")

        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_b64,
            },
        })

    if state.get("user_description"):
        if content:
            text = f"补充说明：{state['user_description']}\n\n请根据 UI 参考图和补充说明，输出需求 Draft。"
        else:
            text = f"UI 描述如下：\n{state['user_description']}\n\n请根据以上 UI 描述，输出需求 Draft。"
    else:
        text = "请根据上面的 UI 参考图，输出需求 Draft。"
    content.append({"type": "text", "text": text})

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=content),
    ]

    response = llm.invoke(messages)
    return {**state, "draft": response.content}


def build_graph():
    graph = StateGraph(RequirementsState)
    graph.add_node("analyze", analyze_image)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", END)
    return graph.compile()


def run(input_data: dict) -> dict:
    app = build_graph()
    result = app.invoke({
        "image_path": input_data.get("image_path", ""),
        "user_description": input_data.get("user_description", ""),
        "draft": None,
    })
    return {"draft": result["draft"]}
