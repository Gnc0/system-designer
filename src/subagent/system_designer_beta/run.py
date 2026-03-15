#!/usr/bin/env python3
"""
系统策划多智能体框架 - 统一入口

用法:
  python run.py --agent <name> --input '<json>' [--session-id <timestamp>]
  python run.py --agent <name> --input @path/to/input.json [--session-id <timestamp>]

可用 Agent:
  requirements_analyzer  需求拆解（分析 UI 参考图，输出需求 Draft）
  system_designer        系统策划（根据需求 Draft 撰写策划案）
  standards_reviewer     规范审查（检查策划案是否符合标准规范）
  prompt_guardian        Prompt 守护（分析对话记录，建议原子级 prompt 更新）
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from tools.save_conversation import save_test_io


def main():
    parser = argparse.ArgumentParser(description="系统策划多智能体框架")
    parser.add_argument(
        "--agent",
        required=True,
        choices=["requirements_analyzer", "system_designer", "standards_reviewer", "prompt_guardian"],
        help="要调用的 Agent 名称",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="JSON 输入字符串，或以 @ 开头的文件路径（如 @input.json）",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="会话时间戳，用于日志文件命名（默认自动生成）",
    )
    args = parser.parse_args()

    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")

    # 加载输入
    if args.input.startswith("@"):
        with open(args.input[1:], encoding="utf-8") as f:
            input_data = json.load(f)
    else:
        input_data = json.loads(args.input)

    # 保存入参到 data/test/
    save_test_io(args.agent, input_data, timestamp=session_id)

    # 路由到对应 Agent
    agent_map = {
        "requirements_analyzer": "agents.requirements_analyzer",
        "system_designer": "agents.system_designer",
        "standards_reviewer": "agents.standards_reviewer",
        "prompt_guardian": "agents.prompt_guardian",
    }

    import importlib
    module = importlib.import_module(agent_map[args.agent])
    result = module.run(input_data)

    # 保存出参到 data/test/
    save_test_io(args.agent, input_data, result, timestamp=session_id)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
