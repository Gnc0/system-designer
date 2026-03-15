"""
规范审查 Agent（A3）

输入:
  document: str   - 待审查的策划案（Markdown 格式）

输出:
  review: str     - 审查报告（Markdown 格式）
"""

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

from config import PROMPTS_DIR


class ReviewerState(TypedDict):
    document: str
    review: Optional[str]


def review_node(state: ReviewerState) -> ReviewerState:
    reviewer_prompt = (PROMPTS_DIR / "standards_reviewer.md").read_text(encoding="utf-8")
    # 动态注入策划标准，确保审查依据始终与 system_designer.md 保持同步
    designer_prompt = (PROMPTS_DIR / "system_designer.md").read_text(encoding="utf-8")

    system = f"""{reviewer_prompt}

---
## 参考：当前策划标准规范（来自 system_designer.md）

{designer_prompt}
"""

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"请审查以下策划案：\n\n{state['document']}"),
    ]

    response = llm.invoke(messages)
    return {**state, "review": response.content}


def build_graph():
    graph = StateGraph(ReviewerState)
    graph.add_node("review", review_node)
    graph.set_entry_point("review")
    graph.add_edge("review", END)
    return graph.compile()


def run(input_data: dict) -> dict:
    app = build_graph()
    result = app.invoke({"document": input_data.get("document", ""), "review": None})
    return {"review": result["review"]}
