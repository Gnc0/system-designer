"""
Session Writer CLI

从 JSON 输入文件读取本次完整对话数据，校验字段完整性后写入 YAML。

用法（由 Claude Code 在 Step 5 调用）：
  python tools/session_writer.py --input /path/to/session_data.json

JSON 输入格式（所有字段均为完整原文，禁止摘要）：
{
  "session_id": "20240101_120000",
  "feature_name": "XX系统",
  "workflow": "write",               # write / review / revision / reverse / reverse_only（必填）
  "image_paths": [...],
  "requirements_draft": "...",       # A2/A4 输出完整原文
  "confirmed_draft": "...",          # 用户确认后的完整原文（reverse 流程中与 requirements_draft 相同）
  "planning_document": "...",        # A1 输出完整策划案原文（必须是全文，不能是路径）
  "planning_document_path": "...",   # 策划案保存路径，如 docs/XX_session.txt（可选，辅助索引）
  "review_result": "...",            # A3 输出完整原文
  "messages": [
    {"role": "user", "content": "（完整原文，禁止摘要）"},
    {"role": "assistant", "content": "（完整原文，禁止摘要）"}
  ]
}
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, SKILL_ROOT


# 各工作流类型必须有实际内容的字段
REQUIRED_FIELDS = {
    "write":        ["feature_name", "requirements_draft", "confirmed_draft", "planning_document", "review_result"],
    "review":       ["feature_name", "planning_document", "review_result"],
    "revision":     ["feature_name", "planning_document", "review_result"],
    "reverse":      ["feature_name", "requirements_draft", "confirmed_draft", "planning_document", "review_result"],
    "reverse_only": ["feature_name", "requirements_draft"],
}

# 用于识别占位内容的特征串（出现则视为未填真实内容）
PLACEHOLDER_PATTERNS = [
    "[A1", "[A2", "[A3", "[A5",
    "（此处", "（待填",
    "调用A", "输出完整策划案", "输出需求Draft",
    "审查后直接修复", "保存文档]",
    "正在启动工作流",
]


def _is_placeholder(value: str) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if len(text) < 2:
        return True
    return any(p in text for p in PLACEHOLDER_PATTERNS)


def _try_fill_planning_document(data: dict) -> None:
    """
    如果 planning_document 为空但 planning_document_path 有效，
    自动从文件读取内容填入 planning_document，确保 YAML 记录完整。
    """
    doc = data.get("planning_document", "")
    if doc and not _is_placeholder(doc):
        return  # 已有内容，无需处理

    doc_path_str = data.get("planning_document_path", "").strip()
    if not doc_path_str:
        return

    doc_path = Path(doc_path_str)
    if not doc_path.is_absolute():
        doc_path = SKILL_ROOT / doc_path

    if doc_path.exists() and doc_path.is_file():
        content = doc_path.read_text(encoding="utf-8").strip()
        if len(content) >= 10:
            data["planning_document"] = content
            print(f"ℹ️  planning_document 已从文件自动读取：{doc_path}")


def validate(data: dict) -> list[str]:
    """校验数据完整性，返回错误列表（空列表表示通过）。"""
    errors = []

    # workflow 为必填基础字段
    workflow = data.get("workflow", "")
    if not workflow:
        errors.append("字段 'workflow' 为空，必须填写 write / review / revision / reverse 之一")
        workflow = "write"  # 降级处理，继续校验其余字段
    elif workflow not in REQUIRED_FIELDS:
        errors.append(f"字段 'workflow' 值非法：{workflow!r}，只接受 write / review / revision / reverse / reverse_only")

    for field in REQUIRED_FIELDS.get(workflow, []):
        value = data.get(field, "")
        if not value:
            errors.append(f"字段 '{field}' 为空")
        elif _is_placeholder(value):
            errors.append(f"字段 '{field}' 疑似未填真实内容（含占位符或摘要）：{str(value)[:80]!r}")

    messages = data.get("messages", [])
    if not messages:
        errors.append("messages 列表为空")
    else:
        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            if _is_placeholder(content):
                errors.append(
                    f"messages[{i}] (role={msg.get('role')}) 疑似占位内容，必须填入完整原文：{str(content)[:80]!r}"
                )

    return errors


def write_session(data: dict) -> str:
    """将 session 数据写入 YAML，返回文件路径字符串。"""
    session_id = data.get("session_id", "unknown")
    sessions_dir = DATA_DIR / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    filepath = sessions_dir / f"{session_id}.yaml"
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="保存完整对话记录为 YAML")
    parser.add_argument("--input", required=True, help="包含完整 session 数据的 JSON 文件路径")
    parser.add_argument("--skip-validation", action="store_true", help="跳过内容完整性校验（不推荐）")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：输入文件不存在 - {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    # 尝试从 planning_document_path 自动补全 planning_document
    _try_fill_planning_document(data)

    if not args.skip_validation:
        errors = validate(data)
        if errors:
            print("❌ Session 数据校验失败，以下字段不完整：", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            print("\n请确保所有字段填入完整原文后重新运行。", file=sys.stderr)
            sys.exit(1)

    filepath = write_session(data)
    print(f"✅ Session 已保存：{filepath}")


if __name__ == "__main__":
    main()
