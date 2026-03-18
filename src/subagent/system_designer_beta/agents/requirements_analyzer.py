"""
需求拆解 Agent（A2）

输入:
  image_path: str        - 图片文件路径（相对于 skill root 或绝对路径）
  user_description: str  - 用户补充说明（可为空字符串）

输出:
  draft: str             - 需求 Draft（Markdown 格式）
"""

import base64
import sys
from pathlib import Path
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROMPTS_DIR, SKILL_ROOT, make_llm

from langchain_core.messages import HumanMessage, SystemMessage


class RequirementsState(TypedDict):
    image_path: str
    user_description: str
    draft: Optional[str]
    input_tokens: int
    output_tokens: int


def analyze_image(state: RequirementsState) -> RequirementsState:
    system_prompt = (PROMPTS_DIR / "requirements_analyzer.md").read_text(encoding="utf-8")
    llm = make_llm()

    content = []

    # 解析图片路径（支持相对路径和绝对路径），为空则跳过图片
    raw_path = state.get("image_path", "").strip()
    if raw_path:
        image_path = Path(raw_path)
        if not image_path.is_absolute():
            image_path = SKILL_ROOT / image_path
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

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

    # 收集 token 使用情况
    usage = response.response_metadata.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    return {
        **state,
        "draft": response.content,
        "input_tokens": state.get("input_tokens", 0) + input_tokens,
        "output_tokens": state.get("output_tokens", 0) + output_tokens,
    }


def build_graph():
    graph = StateGraph(RequirementsState)
    graph.add_node("analyze", analyze_image)
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
    app = _get_app()
    result = app.invoke({
        "image_path": input_data.get("image_path", ""),
        "user_description": input_data.get("user_description", ""),
        "draft": None,
        "input_tokens": 0,
        "output_tokens": 0,
    })
    return {
        "draft": result["draft"],
        "usage": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        }
    }
