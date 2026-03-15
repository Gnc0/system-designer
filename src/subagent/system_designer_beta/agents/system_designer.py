"""
系统策划 Agent（A1）

输入:
  requirements_draft: str  - 用户确认过的需求 Draft

输出:
  document: str            - 完整策划案（Markdown 格式）
"""

import operator
import os
import sys
from pathlib import Path
from typing import Annotated, List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from config import DOCS_DIR, PROMPTS_DIR
from tools.doc_reader import list_directory, read_file


# ── 文档检索工具（A1 按需调用） ──────────────────────────────────────────────

@tool
def query_doc_directory(subdir: str = "") -> str:
    """列出项目策划文档目录下的文件。subdir 为子目录路径（相对于文档根目录），默认列出根目录。"""
    return list_directory(subdir)


@tool
def read_doc_file(relative_path: str) -> str:
    """读取项目策划文档的内容。relative_path 为相对于文档根目录的路径，例如 'B-布阵/B-布阵.xlsx'。
    注意：读取完毕后，你必须从上下文中释放该文档内容，不保留在工作记忆中。"""
    return read_file(relative_path)


TOOLS = [query_doc_directory, read_doc_file]


# ── LangGraph State ──────────────────────────────────────────────────────────

class SystemDesignerState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    requirements_draft: str
    document: Optional[str]


# ── Nodes ────────────────────────────────────────────────────────────────────

def designer_node(state: SystemDesignerState) -> SystemDesignerState:
    system_prompt = (PROMPTS_DIR / "system_designer.md").read_text(encoding="utf-8")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    ).bind_tools(TOOLS)

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ])

    # 如果没有 tool_calls，则这是最终输出
    document = response.content if not response.tool_calls else None
    return {"messages": [response], "document": document}


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


def run(input_data: dict) -> dict:
    app = build_graph()
    draft = input_data.get("requirements_draft", "")
    initial_state = {
        "messages": [
            HumanMessage(content=f"需求草案如下：\n\n{draft}\n\n请根据以上需求草案，撰写完整的系统策划文档。")
        ],
        "requirements_draft": draft,
        "document": None,
    }
    result = app.invoke(initial_state)
    return {"document": result["document"]}
