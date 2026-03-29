---
name: system designer
description: 游戏系统策划多智能体工作流。基于 UI 参考图，自动完成需求拆解、策划案撰写、规范审查的全流程。触发词：写策划案、设计系统、系统设计、策划文档、需求文档、审查策划案、规范审查、修改策划案、逆向需求。
---

# 业务规则

## 术语

| 术语 | 含义 |
|------|------|
| 策划案 | 系统策划文档，描述游戏内功能系统的完整设计 |
| 需求 Draft | 从 UI 参考图提取的结构化需求草案 |
| 规范审查 | 对策划案的格式、语言、逻辑进行合规性检查 |
| 逆向需求 | 从已有策划案还原为标准格式需求 Draft |
| Prompt 守护 | 自动优化策划 Agent 的 system prompt |
| session_id | 本次任务的唯一标识，格式 `%Y%m%d_%H%M%S` |

## 约束

1. **永远不要**在没有 UI 参考图的情况下开始写策划案（至少需要图片或文字描述之一）
2. **永远不要**跳过用户对需求 Draft 的确认步骤
3. **所有子代理通过 agent 名称直接调用**（sd-a1 ~ sd-a5），禁止 read prompt 文件再传入
4. **所有生成的策划案必须保存到 `docs/` 目录**
5. **规范审查后如有修改**：必须先经用户确认，再启动子代理用 `edit` 工具编辑策划案文件。禁止由主线程直接修改

## 子代理调用

- 使用 `subagent` 工具的 SINGLE 模式调用
- system prompt 由 pi 框架自动注入（`~/.pi/agent/agents/sd-*.md`）
- `task` 参数只包含用户数据，禁止附加与 agent system prompt 冲突的指令

## Agent 定义

| Agent | 用途 | 内部规范 |
|-------|------|----------|
| `sd-a1` | 策划案撰写/修改 | `agents/sd-a1.md`（格式、语言、结构等规范） |
| `sd-a2` | UI 需求拆解 | `agents/sd-a2.md`（拆解模板） |
| `sd-a3` | 规范审查 | `agents/sd-a3.md`（审查标准） |
| `sd-a4` | 逆向需求 | `agents/sd-a4.md`（逆向规则） |
| `sd-a5` | Prompt 守护 | `agents/sd-a5.md`（守护规则） |

## vision_describe 调用方式
通过 MCP 服务器将图片转为结构化文字描述，供文本模型理解 UI 图。

```bash
vision_describe(image_path: "data/images/{session_id}_ref.png")
vision_describe(image_path: "data/images/{session_id}_ref.png", provider: "kimi", model: "kimi-k2.5")
```

支持的 provider：`kimi` / `moonshot` / `anthropic` / `openai`。

不指定 provider 时按 `config.json` → `VISION_PROVIDER` 环境变量 → 默认值（kimi）。

API Key 优先级：`VISION_API_KEY` 环境变量 > `config.json`。

MCP 服务器需在 pi 的 `settings.json` 中注册（详见 README.md），配置路径指向 `src/vision-describe-mcp/`。

---

# 工作流

## 一、写策划案（主流程）

**Step 1：获取 UI 参考图**

提示语：「请提供该功能的 UI 参考图，可直接在对话中粘贴截图或拖入图片文件。」

**Step 1.5：视觉理解（如需）**

若主控或子代理无法直接理解图片：
1. 保存图片到 `data/images/{session_id}_ref.png`
2. `vision_describe(image_path: "data/images/{session_id}_ref.png")`
3. 将描述文本作为「图片描述」传入后续步骤

**Step 2：调用需求拆解（sd-a2）**

```
subagent SINGLE: { agent: "sd-a2", task: "以下是用户提供的 UI 参考图描述和说明：\n\n{图片描述}\n\n{用户补充说明}" }
```

→ 展示 Draft → **等待用户确认** → 保存为 `docs/{session_id}_confirmed_draft.md`

**Step 3：调用策划案撰写（sd-a1）**

```
subagent SINGLE: { agent: "sd-a1", task: "请根据需求文档撰写策划案。需求文档路径：docs/{session_id}_confirmed_draft.md\n\nsession_id: {session_id}\n\n如需查阅项目历史文档，请使用 read 工具读取 docs/project_doc_index.md 中对应的文件。" }
```

**Step 4：自动调用规范审查（sd-a3）**

```
subagent SINGLE: { agent: "sd-a3", task: "请审查以下策划案：docs/{session_id}_{docs_name}.md" }
```

→ 展示审查报告 → **等待用户确认修改项**

**Step 5：调用 Prompt 守护（sd-a5）**

```
subagent SINGLE: { agent: "sd-a5", task: "本次对话摘要：\n\n{对话要点摘要}" }
```

→ 如有建议，展示 diff → **等待用户确认** → 执行建议（由sd-a5控制原子操作）

## 二、审查策划案

```
subagent SINGLE: { agent: "sd-a3", task: "请审查以下策划案内容：\n\n{用户粘贴的策划案}" }
```

## 三、修改策划案

```
subagent SINGLE: { agent: "sd-a1", task: "请修改策划案 docs/{session_id}_{docs_name}.md，修改要求：\n\n{用户修改意见}\n\n请使用 edit 工具直接编辑该文件，逐一修正后输出修改摘要。" }
```

修改后自动调用 A3 审查。

## 四、逆向需求

1. 读取 `docs/project_doc_index.md` 查找文档（`.xlsx` 用 `src/xlsx_to_md.py` 转换）
2. `subagent SINGLE: { agent: "sd-a4", task: "请将以下策划案逆向拆解为需求 Draft：\n\n{策划案文本}" }`
3. 取 Part 1（`---` 之前）→ `subagent SINGLE: { agent: "sd-a1", task: "请根据以下需求文档撰写策划案：\n\n{Part 1}\n\nsession_id: {session_id}" }`
4. 自动调用 A3 审查
