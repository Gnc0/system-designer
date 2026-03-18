import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Skill root: 4 levels up from this file
# this file: src/subagent/system_designer_beta/config.py
SKILL_ROOT = Path(__file__).parent.parent.parent.parent.resolve()

PROMPTS_DIR = SKILL_ROOT / "prompts"
DATA_DIR = SKILL_ROOT / "data"
DOCS_DIR = SKILL_ROOT / "docs"

MODEL_NAME = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def make_llm(**kwargs):
    """创建 ChatAnthropic 实例，统一管理模型名和 API Key。"""
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=MODEL_NAME,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        **kwargs,
    )
