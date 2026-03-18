"""
规范审查 Agent（A3）

输入:
  document: str   - 待审查的策划案（Markdown 格式）

输出:
  review: str     - 审查报告（Markdown 格式）
"""

import sys
from pathlib import Path
from typing import Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROMPTS_DIR, make_llm


class ReviewerState(TypedDict):
    document: str
    review: Optional[str]
    input_tokens: int
    output_tokens: int


def review_node(state: ReviewerState) -> ReviewerState:
    reviewer_prompt = (PROMPTS_DIR / "standards_reviewer.md").read_text(encoding="utf-8")
    # 动态注入策划标准，确保审查依据始终与 system_designer.md 保持同步
    designer_prompt = (PROMPTS_DIR / "system_designer.md").read_text(encoding="utf-8")

    system = f"""{reviewer_prompt}

---
## 参考：当前策划标准规范（来自 system_designer.md）

{designer_prompt}
"""

    llm = make_llm()

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"请审查以下策划案：\n\n{state['document']}"),
    ]

    response = llm.invoke(messages)

    # 收集 token 使用情况
    usage = response.response_metadata.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    return {
        **state,
        "review": response.content,
        "input_tokens": state.get("input_tokens", 0) + input_tokens,
        "output_tokens": state.get("output_tokens", 0) + output_tokens,
    }


def build_graph():
    graph = StateGraph(ReviewerState)
    graph.add_node("review", review_node)
    graph.set_entry_point("review")
    graph.add_edge("review", END)
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
        "document": input_data.get("document", ""),
        "review": None,
        "input_tokens": 0,
        "output_tokens": 0,
    })
    return {
        "review": result["review"],
        "usage": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        }
    }
