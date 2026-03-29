# System Designer

游戏系统策划多智能体工作流。基于 UI 参考图，自动完成需求拆解、策划案撰写、规范审查的全流程。

## 功能

- **UI 需求拆解** — 从参考图提取结构化需求 Draft
- **策划案撰写** — 基于需求生成标准格式策划案
- **规范审查** — 自动检查格式、语言、逻辑合规性
- **逆向需求** — 从已有策划案还原需求 Draft
- **Prompt 守护** — 自动优化策划 Agent 的 system prompt

## 设计理念

- **多智能体协作**：策划、需求、审查、守护 5 个 Agent 各司其职
- **pi 框架原生**：使用 pi 的 skill + agents 机制，零配置启动
- **无视觉能力也能用**：vision_describe MCP 支持 Kimi k2.5、Claude、OpenAI 等视觉模型
- **可观测性**：所有对话和输出保存在 `data/sessions/`，便于回溯

## 架构

```
用户输入 UI 参考
    ↓
pi (Supervisor)
    ↓ sd-a2 (需求拆解)
需求 Draft
    ↓ 用户确认
    ↓ sd-a1 (策划撰写) → sd-a5 (Prompt 守护)
策划案
    ↓ sd-a3 (规范审查)
审查报告
    ↓ 用户确认修改
最终策划案
```

## 目录结构

```
system-designer/
├── SKILL.md                          ← 业务规则 + 工作流（pi 加载）
├── README.md                         ← 本文件
├── agents/
│   ├── sd-a1.md ~ sd-a5.md           ← Agent 定义
├── src/vision-describe-mcp/        ← 视觉理解 MCP 服务器
│   ├── server.py
│   ├── config.example.json
│   └── requirements.txt
├── docs/                             ← 策划案输出
├── data/                             → 图片、对话记录
└── src/xlsx_to_md.py                 ← Excel 转换工具
```

## Agent 概览

| Agent | 用途 |
|-------|------|
| `sd-a1` | 策划撰写/修改（受 sd-a5 守护） |
| `sd-a2` | UI 需求拆解 |
| `sd-a3` | 规范审查 |
| `sd-a4` | 逆向需求 |
| `sd-a5` | Prompt 守护 |

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/your-username/system-designer.git
cd system-designer
```

### 2. 注册 Agent 定义

```bash
# Linux / macOS
for f in agents/sd-*.md; do
  ln -sf "$(pwd)/$f" ~/.pi/agent/agents/$(basename "$f")
done

# Windows（管理员 CMD）
mklink "%USERPROFILE%\.pi\agent\agents\sd-a1.md" "%cd%\agents\sd-a1.md"
mklink "%USERPROFILE%\.pi\agent\agents\sd-a2.md" "%cd%\agents\sd-a2.md"
mklink "%USERPROFILE%\.pi\agent\agents\sd-a3.md" "%cd%\agents\sd-a3.md"
mklink "%USERPROFILE%\.pi\agent\agents\sd-a4.md" "%cd%\agents\sd-a4.md"
mklink "%USERPROFILE%\.pi\agent\agents\sd-a5.md" "%cd%\agents\sd-a5.md"
```

验证：`subagent { action: "list" }` 应看到 `sd-a1` ~ `sd-a5`。

### 3. 安装视觉 MCP 服务器（可选）

```bash
cd src/vision-describe-mcp
pip install -r requirements.txt
cp config.example.json config.json
# 编辑 config.json，填入 apiKey
```

`config.json` 示例：

```json
{
  "provider": "kimi",
  "model": "kimi-k2.5",
  "base_url": "https://api.moonshot.cn/v1",
  "api_key": "sk-xxxxx"
}
```

支持的 Provider：`kimi` / `moonshot` / `anthropic` / `openai`。

在 pi 的 `settings.json` 中注册 MCP 服务器：

```json
{
  "mcpServers": {
    "vision-describe": {
      "command": "python",
      "args": ["/path/to/src/vision-describe-mcp/server.py"],
      "cwd": "/path/to/src/vision-describe-mcp"
    }
  }
}
```

注册后 `/reload` 生效。

### 4. 在 pi 中使用

```bash
pi --skill $(pwd)
# 然后触发：写策划案
```

## 使用示例

```
用户：写策划案
pi：请提供该功能的 UI 参考图
用户：[粘贴截图]
pi：[调用 vision_describe] → [调用 sd-a2 拆解需求] →
     需求 Draft 已生成，请确认：
     1. 玩家进入商城，点击充值按钮
     2. 选择充值档位 648 元
     ...
用户：确认
pi：[调用 sd-a1 撰写策划案] → [调用 sd-a3 规范审查] →
     策划案已生成：docs/20250328_103045_充值系统.md
     审查结果：2 处修改建议
```

## FAQ

**Q：不安装 vision_describe 能用吗？**
A：可以。直接用文字描述 UI 参考，或由你粘贴策划案让 sd-a4 逆向生成需求。

**Q：可以自定义策划案格式吗？**
A：修改 `agents/sd-a1.md` 的 body 部分。`sd-a5` 守护 Agent 会持续优化它。

**Q：历史文档如何索引？**
A：更新 `docs/project_doc_index.md`，`sd-a1` 会自动读取参考。

**Q：想用 Kimi 做视觉理解？**
A：在 `config.json` 中设置 `provider: "kimi"`，`model: "kimi-k2.5"`，填入 `api_key` 即可。

## License

MIT

---

本项目基于 [pi](https://github.com/mariozechner/pi) 构建。
