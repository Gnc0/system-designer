# Vision Describe MCP Server

视觉理解 MCP 服务器。通过 vision-capable 模型（Kimi k2.5 / Claude / GPT-4o）将图片转换为结构化文字描述。

## 安装

```bash
cd extensions/vision-describe-mcp
pip install -r requirements.txt
```

## 配置

复制 `config.example.json` → `config.json`，填入 API Key：

```json
{
  "provider": "kimi",
  "model": "kimi-k2.5",
  "base_url": "https://api.moonshot.cn/v1",
  "api_key": "sk-xxxxx"
}
```

支持的 provider：`kimi` / `anthropic` / `openai`

## 运行

### stdio 模式（推荐，适用于 pi / Claude Code 等）

```bash
python server.py
```

### SSE 模式（适用于 Web 客户端）

```bash
python server.py --transport sse --port 8000
```

## 在 pi 中使用

在 `~/.pi/settings.json` 或项目 `.pi/settings.json` 中配置：

```json
{
  "mcpServers": {
    "vision-describe": {
      "command": "python",
      "args": ["G:/path/to/extensions/vision-describe-mcp/server.py"],
      "cwd": "G:/path/to/extensions/vision-describe-mcp"
    }
  }
}
```

注册后 `/reload`，即可使用 `vision_describe` 工具。

## 工具

### `vision_describe`

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `image_path` | string | ✅ | 图片路径（png/jpg/jpeg/gif/webp/bmp） |
| `prompt` | string | ❌ | 自定义描述指令（默认：UI 详细分析） |
| `provider` | string | ❌ | 覆盖 provider（kimi/anthropic/openai） |
| `model` | string | ❌ | 覆盖模型名称 |

## 环境变量（可选，优先于 config.json）

| 变量 | 说明 |
|------|------|
| `VISION_API_KEY` | API Key |
| `VISION_PROVIDER` | provider 名称 |
| `VISION_MODEL` | 模型名称 |
| `VISION_BASE_URL` | API base URL |
