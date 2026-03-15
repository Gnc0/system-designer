"""
对话记录与传参保存工具

负责：
- 保存完整会话记录到 data/sessions/{timestamp}.yaml
- 保存每次 Agent 调用的 input/output 到 data/test/
- 保存用户上传的图片到 data/images/
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR


def save_session(session_data: dict, timestamp: str = None) -> str:
    """保存完整会话记录为 YAML，返回文件路径。"""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    sessions_dir = DATA_DIR / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    filepath = sessions_dir / f"{timestamp}.yaml"
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(session_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return str(filepath)


def save_test_io(agent_name: str, input_data: dict, output_data: dict = None, timestamp: str = None) -> dict:
    """保存 Agent 调用的 input 和 output 到 data/test/，用于调试。"""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    test_dir = DATA_DIR / "test"
    test_dir.mkdir(parents=True, exist_ok=True)

    input_path = test_dir / f"{timestamp}_{agent_name}_input.json"
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, ensure_ascii=False, indent=2)

    paths = {"input": str(input_path)}

    if output_data is not None:
        output_path = test_dir / f"{timestamp}_{agent_name}_output.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        paths["output"] = str(output_path)

    return paths


def save_image(image_bytes: bytes, original_name: str, timestamp: str = None) -> str:
    """保存用户上传的图片到 data/images/，返回保存路径（相对于 skill root）。"""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    images_dir = DATA_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    filepath = images_dir / f"{timestamp}_{original_name}"
    filepath.write_bytes(image_bytes)

    # 返回相对于 skill root 的路径，供 claude.md 工作流引用
    from config import SKILL_ROOT
    return str(filepath.relative_to(SKILL_ROOT))
