"""
测试 run.py 模块
"""
import json
import pytest
from pathlib import Path


def test_validate_input_valid():
    """测试输入验证 - 有效输入"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from run import validate_input
    
    # 有效的 requirements_analyzer 输入
    input_data = {
        "image_path": "test.png",
        "user_input": "设计一个签到系统"
    }
    # 不应该抛出异常
    validate_input(input_data, "requirements_analyzer")


def test_validate_input_invalid_type():
    """测试输入验证 - 无效类型"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from run import validate_input, InputValidationError
    
    # 输入不是字典
    with pytest.raises(InputValidationError):
        validate_input("not a dict", "requirements_analyzer")


def test_validate_input_missing_fields():
    """测试输入验证 - 缺少字段（应该警告但不报错）"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from run import validate_input
    
    # 缺少 image_path，应该只警告不报错
    input_data = {"user_input": "设计一个签到系统"}
    validate_input(input_data, "requirements_analyzer")


def test_run_agent_unknown():
    """测试执行未知 Agent"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "subagent" / "system_designer_beta"))
    
    from run import run_agent, AgentError
    
    with pytest.raises(AgentError):
        run_agent("unknown_agent", {})


def test_json_parsing():
    """测试 JSON 解析"""
    # 有效的 JSON
    valid_json = '{"key": "value"}'
    result = json.loads(valid_json)
    assert result == {"key": "value"}
    
    # 无效的 JSON
    invalid_json = '{"key": value}'
    with pytest.raises(json.JSONDecodeError):
        json.loads(invalid_json)