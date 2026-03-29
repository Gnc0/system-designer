"""
Vision Describe MCP Server
==========================
将图片发送给视觉模型（Kimi k2.5 / Claude / GPT-4o），返回结构化文字描述。

用法:
    python server.py                          # stdio 模式（默认）
    python server.py --transport sse --port 8000  # SSE 模式

配置:
    在同目录放置 config.json（参考 config.example.json）
    也可通过环境变量配置（VISION_API_KEY / VISION_PROVIDER / VISION_MODEL / VISION_BASE_URL）
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
TIMEOUT_SECONDS = 120

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

EXT_MEDIA_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

DEFAULT_SYSTEM_PROMPT = """你是一个专业的 UI 截图文字提取与视觉描述工具。你的唯一任务是**忠实地提取和描述图片中可见的内容**。

## 严格禁止
- 禁止猜测或推断系统名称、功能类型、页面用途
- 禁止使用"推测""可能""应该是"等推断性表述
- 禁止描述图片中不存在的内容

## 描述要求
1. **完整文字提取（最重要）**：逐字逐句提取图片中的所有可见文字，包括但不限于：标题、按钮文案、标签文字、数值、提示信息、Tab 名称、列表条目中的文字。对于不确定的字，用 [?] 标注。
2. **整体布局**：描述页面的空间结构（顶部/中部/底部/左侧/右侧各有什么区域）
3. **UI 元素**：客观描述可见元素（按钮、标签、列表条目、图标、弹窗、进度条等）的形状、位置、数量
4. **颜色与样式**：描述元素的颜色和视觉样式
5. **层级关系**：描述元素之间的遮挡、包含、并列关系
6. **数值信息**：提取所有可见数值

## 输出格式
使用结构化 Markdown。按"完整文字提取 → 布局 → 元素 → 样式 → 数值"的顺序组织。"""

PROVIDERS = {
    "kimi": {
        "default_model": "kimi-k2.5",
        "base_url": "https://api.moonshot.cn/v1",
        "api_type": "openai",
    },
    "moonshot": {
        "default_model": "moonshot-v1-128k",
        "base_url": "https://api.moonshot.cn/v1",
        "api_type": "openai",
    },
    "openai": {
        "default_model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
        "api_type": "openai",
    },
    "anthropic": {
        "default_model": "claude-sonnet-4-5-20250514",
        "base_url": "https://api.anthropic.com",
        "api_type": "anthropic",
    },
}


def _load_config() -> dict:
    """从 config.json 加载配置，找不到则返回空 dict。"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text("utf-8"))
        except Exception:
            return {}
    return {}


def _resolve(key: str, param: Optional[str], fallback: str = "") -> str:
    """按优先级解析配置值：工具参数 > 环境变量 > config.json > 默认值"""
    env_key = f"VISION_{key.upper()}"
    env_map = {"api_key": "VISION_API_KEY", "base_url": "VISION_BASE_URL",
               "provider": "VISION_PROVIDER", "model": "VISION_MODEL"}
    env_val = os.environ.get(env_map.get(key, env_key))
    if param:
        return param
    if env_val:
        return env_val
    cfg = _load_config()
    return cfg.get(key, fallback)


# ---------------------------------------------------------------------------
# API 调用
# ---------------------------------------------------------------------------

async def _call_openai_compatible(
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    image_base64: str,
    media_type: str,
    timeout: int = TIMEOUT_SECONDS,
) -> str:
    """调用 OpenAI 兼容 API（Kimi / Moonshot / OpenAI）"""
    image_url = f"data:{media_type};base64,{image_base64}"
    url = base_url.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                            {"type": "text", "text": user_prompt},
                        ],
                    },
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise ValueError("API 返回空内容")
        return content


async def _call_anthropic(
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    image_base64: str,
    media_type: str,
    timeout: int = TIMEOUT_SECONDS,
) -> str:
    """调用 Anthropic Messages API"""
    url = base_url.rstrip("/") + "/v1/messages"

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": api_key,
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {"type": "text", "text": user_prompt},
                        ],
                    },
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        texts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
        if not texts:
            raise ValueError("Anthropic API 返回空内容")
        return "\n".join(texts)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="vision-describe",
    instructions=(
        "视觉理解工具。将图片发送给视觉模型，返回结构化的 UI/图片描述。"
        "支持 Kimi k2.5、Claude、GPT-4o 等 provider。"
        "配置文件：同目录下的 config.json。"
        "环境变量优先级高于配置文件。"
    ),
)


@mcp.tool()
async def vision_describe(
    image_path: str,
    prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    使用视觉模型描述图片内容。

    Args:
        image_path: 图片文件路径（支持 png/jpg/jpeg/gif/webp/bmp，最大 20MB）
        prompt: 自定义描述指令。默认为 UI 详细分析。
        provider: 视觉模型 provider（kimi/moonshot/openai/anthropic）。默认从配置读取。
        model: 模型名称。默认从配置读取。

    Returns:
        结构化 Markdown 格式的图片描述文本。
    """
    # --- 解析路径 ---
    abs_path = Path(image_path).expanduser().resolve()
    if not abs_path.exists():
        raise FileNotFoundError(f"图片不存在: {abs_path}")

    ext = abs_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"不支持的格式: {ext}。支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # --- 读取 & 校验大小 ---
    image_data = abs_path.read_bytes()
    if len(image_data) > MAX_IMAGE_SIZE:
        raise ValueError(
            f"图片过大: {len(image_data) / 1024 / 1024:.1f} MB "
            f"（最大 {MAX_IMAGE_SIZE / 1024 / 1024:.0f} MB）"
        )

    # --- 解析 provider ---
    provider_name = _resolve("provider", provider, "kimi")
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"不支持的 provider: {provider_name}。"
            f"支持: {', '.join(PROVIDERS.keys())}"
        )
    prov_cfg = PROVIDERS[provider_name]

    # --- 解析 API key ---
    api_key = _resolve("api_key", None, "")
    if not api_key:
        raise ValueError(
            "未配置 API Key。请通过以下方式之一配置：\n"
            "  1. 在 config.json 中设置 api_key\n"
            "  2. 设置环境变量 VISION_API_KEY\n"
            "  3. 通过 provider/model 参数指定"
        )

    # --- 解析 model & base_url ---
    model_name = _resolve("model", model, prov_cfg["default_model"])
    base_url = _resolve("base_url", None, prov_cfg["base_url"])

    media_type = EXT_MEDIA_MAP.get(ext, "image/png")
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    user_prompt = prompt or (
        "请详细描述这张 UI 参考图中的所有视觉元素。"
        "按照整体布局、UI 元素、文字内容、颜色与状态、层级关系、数值信息分类描述。"
    )

    # --- 调用 API ---
    if prov_cfg["api_type"] == "anthropic":
        result = await _call_anthropic(
            api_key, base_url, model_name,
            DEFAULT_SYSTEM_PROMPT, user_prompt,
            image_base64, media_type,
        )
    else:
        result = await _call_openai_compatible(
            api_key, base_url, model_name,
            DEFAULT_SYSTEM_PROMPT, user_prompt,
            image_base64, media_type,
        )

    # 拼接元信息头
    header = (
        f"<!-- vision-describe | provider={provider_name} | model={model_name} "
        f"| size={len(image_data) / 1024:.0f}KB | type={media_type} -->\n\n"
    )
    return header + result


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Vision Describe MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="传输协议（默认 stdio）",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="SSE 模式监听地址（默认 0.0.0.0）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="SSE 模式监听端口（默认 8000）",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
