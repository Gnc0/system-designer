"""
Prompt 原子更新工具

负责将 prompt_guardian 建议的原子操作（一句话增/删/改）应用到 prompt 文件。
调用前必须经过用户文字确认。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROMPTS_DIR


def apply_suggestion(prompt_name: str, suggestion: dict) -> dict:
    """
    将一条原子建议应用到 prompt 文件。

    Args:
        prompt_name: prompt 文件名（不含 .md），如 "system_designer"
        suggestion: {
            "action": "add" | "delete" | "modify",
            "location": "...",
            "original": "...",   # delete/modify 必填
            "new": "...",        # add/modify 必填
            "reason": "..."
        }

    Returns:
        {"success": bool, "message": str}
    """
    path = PROMPTS_DIR / f"{prompt_name}.md"
    if not path.exists():
        return {"success": False, "message": f"Prompt 文件不存在: {prompt_name}.md"}

    content = path.read_text(encoding="utf-8")
    action = suggestion.get("action", "")

    if action == "delete":
        original = suggestion.get("original", "").strip()
        if not original:
            return {"success": False, "message": "delete 操作必须提供 original 字段"}
        if original not in content:
            return {"success": False, "message": f"未在文件中找到目标句子：\n  {original}"}
        # 删除该句及其后的换行符
        new_content = content.replace(original + "\n", "").replace(original, "")
        path.write_text(new_content, encoding="utf-8")
        return {"success": True, "message": f"已删除：{original}"}

    elif action == "modify":
        original = suggestion.get("original", "").strip()
        new = suggestion.get("new", "").strip()
        if not original or not new:
            return {"success": False, "message": "modify 操作必须提供 original 和 new 字段"}
        if original not in content:
            return {"success": False, "message": f"未在文件中找到目标句子：\n  {original}"}
        new_content = content.replace(original, new, 1)
        path.write_text(new_content, encoding="utf-8")
        return {"success": True, "message": f"已修改：\n  原：{original}\n  新：{new}"}

    elif action == "add":
        new = suggestion.get("new", "").strip()
        location = suggestion.get("location", "").strip()
        if not new:
            return {"success": False, "message": "add 操作必须提供 new 字段"}
        if location and location in content:
            new_content = content.replace(location, location + "\n" + new, 1)
        else:
            new_content = content.rstrip() + "\n" + new + "\n"
        path.write_text(new_content, encoding="utf-8")
        return {"success": True, "message": f"已追加：{new}"}

    else:
        return {"success": False, "message": f"未知操作类型：{action}（只支持 add / delete / modify）"}
