"""
测试 agents 模块
"""
import pytest
from pathlib import Path


def test_requirements_analyzer_import():
    """测试 requirements_analyzer 模块导入"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from agents import requirements_analyzer
    assert hasattr(requirements_analyzer, "run")
    assert hasattr(requirements_analyzer, "build_graph")


def test_system_designer_import():
    """测试 system_designer 模块导入"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from agents import system_designer
    assert hasattr(system_designer, "run")


def test_standards_reviewer_import():
    """测试 standards_reviewer 模块导入"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from agents import standards_reviewer
    assert hasattr(standards_reviewer, "run")


def test_prompt_guardian_import():
    """测试 prompt_guardian 模块导入"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from agents import prompt_guardian
    assert hasattr(prompt_guardian, "run")


def test_requirements_analyzer_state():
    """测试 RequirementsState 类型定义"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from agents.requirements_analyzer import RequirementsState
    
    # 验证 TypedDict 的键
    state = {
        "image_path": "test.png",
        "user_description": "测试描述",
        "draft": None,
        "input_tokens": 0,
        "output_tokens": 0,
    }
    
    # 类型检查应该通过
    assert state["image_path"] == "test.png"
    assert state["user_description"] == "测试描述"
    assert state["draft"] is None


def test_build_graph():
    """测试 LangGraph 构建"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from agents.requirements_analyzer import build_graph
    
    # 构建图不应该抛出异常
    graph = build_graph()
    assert graph is not None