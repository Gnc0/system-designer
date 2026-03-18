"""
系统策划 Agent（A1）

输入:
  requirements_draft: str  - 用户确认过的需求 Draft

输出:
  document: str            - 完整策划案（Markdown 格式）
"""

import operator
import sys
from pathlib import Path
from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DOCS_DIR, PROMPTS_DIR, make_llm
from tools.doc_reader import list_directory, read_file


# ── 文档检索工具（A1 按需调用） ──────────────────────────────────────────────

@tool
def query_doc_directory(subdir: str = "") -> str:
    """列出项目文档目录下的文件。subdir 为子目录路径（相对于文档根目录），默认列出根目录。"""
    return list_directory(subdir)


@tool
def read_doc_file(relative_path: str) -> str:
    """读取项目历史文档的内容。relative_path 为相对于文档根目录的路径，例如 'B-布阵/B-布阵.xlsx'。
    注意：读取完毕后，你必须从上下文中释放该文档内容，不保留在工作记忆中。"""
    return read_file(relative_path)


TOOLS = [query_doc_directory, read_doc_file]


# ── LangGraph State ──────────────────────────────────────────────────────────

class SystemDesignerState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    requirements_draft: str
    document: Optional[str]
    input_tokens: int
    output_tokens: int


# ── Nodes ────────────────────────────────────────────────────────────────────

def designer_node(state: SystemDesignerState) -> SystemDesignerState:
    system_prompt = (PROMPTS_DIR / "system_designer.md").read_text(encoding="utf-8")
    llm = make_llm().bind_tools(TOOLS)

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ])

    # 收集 token 使用情况
    usage = response.response_metadata.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # 如果没有 tool_calls，则这是最终输出
    document = response.content if not response.tool_calls else None
    return {
        "messages": [response],
        "document": document,
        "input_tokens": state.get("input_tokens", 0) + input_tokens,
        "output_tokens": state.get("output_tokens", 0) + output_tokens,
    }


def should_continue(state: SystemDesignerState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(SystemDesignerState)
    graph.add_node("designer", designer_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("designer")
    graph.add_conditional_edges("designer", should_continue)
    graph.add_edge("tools", "designer")
    return graph.compile()


_app = None


def _get_app():
    global _app
    if _app is None:
        _app = build_graph()
    return _app


def run(input_data: dict) -> dict:
    app = _get_app()
    draft = input_data.get("requirements_draft", "")
    initial_state = {
        "messages": [
            HumanMessage(content=f"需求草案如下：\n\n{draft}\n\n请根据以上需求草案，撰写完整的系统策划文档。")
        ],
        "requirements_draft": draft,
        "document": None,
        "input_tokens": 0,
        "output_tokens": 0,
    }
    result = app.invoke(initial_state)
    return {
        "document": result["document"],
        "usage": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        }
    }
