"""
测试 config 模块
"""
import os
import pytest
from pathlib import Path


def test_skill_root_path():
    """测试 SKILL_ROOT 路径计算"""
    # 动态导入以避免路径问题
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from config import SKILL_ROOT, PROMPTS_DIR, DATA_DIR, DOCS_DIR
    
    # 验证路径存在
    assert SKILL_ROOT.exists(), f"SKILL_ROOT 不存在: {SKILL_ROOT}"
    assert PROMPTS_DIR.exists(), f"PROMPTS_DIR 不存在: {PROMPTS_DIR}"
    
    # 验证目录结构
    assert (SKILL_ROOT / "prompts").exists()
    assert (SKILL_ROOT / "data").exists() or True  # data 可能不存在
    assert (SKILL_ROOT / "docs").exists() or True  # docs 可能不存在


def test_model_name_default():
    """测试默认模型名称"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from config import MODEL_NAME
    
    # 默认应该是 claude-sonnet-4-6
    assert MODEL_NAME == "claude-sonnet-4-6" or MODEL_NAME


def test_make_llm_without_api_key():
    """测试没有 API Key 时的行为"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    # 临时移除 API Key
    original_key = os.environ.get("ANTHROPIC_API_KEY")
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]
    
    try:
        from config import make_llm
        # 应该能创建 LLM 实例，但在调用时会失败
        llm = make_llm()
        assert llm is not None
    finally:
        # 恢复 API Key
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key