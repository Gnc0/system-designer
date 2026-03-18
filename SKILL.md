---
name: system designer
description: 项目系统策划多智能体工作流。基于 UI 参考图，自动完成需求拆解、策划案撰写、规范审查的全流程。触发词：写策划案、设计系统、系统设计、策划文档、需求文档、审查策划案、规范审查、修改策划案。
---

# System Designer Skill

项目系统策划多智能体工作流。基于 UI 参考图，自动完成需求拆解、策划案撰写、规范审查的全流程。

> **注意**：本 skill 的完整工作流配置在 `CLAUDE.md`（Claude Code Supervisor 配置）中。
> OpenClaw 加载本 SKILL.md 后，具体执行逻辑请参考 CLAUDE.md。

## 工作流程

### 一、写策划案（主流程）

**Step 1：索取 UI 参考图（必须，不可跳过）**
- 检测到"写策划案"、"帮我设计XX系统"等意图时，立刻要求用户提供 UI 参考图
- 提示语：「请提供该功能的 UI 参考图，可直接在对话中粘贴截图或拖入图片文件。」
- 用户不提供则不继续，耐心等待
- 收到图片后，保存到 `data/images/{session_id}_{原始文件名或 ref.png}`

**Step 2：调用需求拆解 Agent（A2）**
- 使用 `sessions_spawn` 调用子代理，传入 `prompts/requirements_analyzer.md` 全文作为 System Prompt
- 将图片描述和用户说明作为用户输入传入
- 将输出的需求 Draft **完整展示**给用户
- **必须等待用户明确确认**（「确认」或「修改如下：...」），不得跳过此步骤

**Step 3：调用系统策划 Agent（A1）**
- 使用 `sessions_spawn` 调用子代理，传入 `prompts/system_designer.md` 全文作为 System Prompt
- 将 confirmed_draft 作为用户输入传入
- 如需查阅项目历史文档，参考 `docs/project_doc_index.md`
- 输出：完整策划案文档

**Step 4：自动调用规范审查 Agent（A3）**
- 使用 `sessions_spawn` 调用子代理，传入 `prompts/standards_reviewer.md` 全文作为 System Prompt
- 将策划案作为用户输入传入
- 将审查结果附在策划案后展示
- 格式：先输出策划案，再输出「---\n## 规范审查报告」分隔块
- **审查报告展示后，必须等待用户明确确认**哪些问题需要修改

**Step 5：保存对话记录**
- 通过 `session_writer.py` 保存完整对话到 `data/sessions/{session_id}.yaml`
- 所有文本字段必须是对应 Agent 的完整输出原文，禁止摘要或截断

**Step 6：调用 Prompt 守护 Agent（A5）**
- 使用 `sessions_spawn` 调用子代理，传入 `prompts/prompt_guardian.md` 全文作为 System Prompt
- 若 A5 建议更新，将 diff 完整展示给用户，等待文字确认
- 每次只执行一条建议，每条建议只涉及一句话（原子操作）

### 二、审查策划案

当用户说「帮我审查这份策划案」时：
1. 要求用户粘贴策划案内容
2. 直接调用 A3（跳过 A1、A2）
3. 展示审查报告
4. 保存对话到 `data/sessions/{session_id}.yaml`

### 三、修改策划案

当用户说「修改XXX」时：
1. 将原策划案 + 修改意见合并，传给 A1
2. A1 输出修改后版本
3. 自动调用 A3 审查
4. 保存 YAML

### 四、逆向需求

当用户说「逆向需求」、「从策划案还原需求」等意图时：
1. 读取 `docs/project_doc_index.md`，找到对应文档路径
2. 调用 A4（`prompts/reverse_requirements.md`）生成逆向需求 Draft
3. 自动调用 A1 生成标准格式策划案
4. 自动调用 A3 规范审查
5. 保存对话记录（workflow: "reverse"）

## 核心文件

- `CLAUDE.md` - Supervisor 完整工作流配置（Claude Code 格式，含详细规范）
- `prompts/system_designer.md` - A1 系统策划 Agent 的 Prompt（受守护）
- `prompts/requirements_analyzer.md` - A2 需求拆解 Agent 的 Prompt
- `prompts/standards_reviewer.md` - A3 规范审查 Agent 的 Prompt
- `prompts/reverse_requirements.md` - A4 逆向需求 Agent 的 Prompt
- `prompts/prompt_guardian.md` - A5 Prompt 守护 Agent 的 Prompt
- `docs/project_doc_index.md` - 项目历史文档目录索引

## 注意事项

- **永远不要**在没有 UI 参考图的情况下开始写策划案
- **永远不要**跳过用户对需求 Draft 的确认步骤
- **所有生成的策划案必须保存到 `docs/` 目录**，文件名格式：`{feature_name}_{session_id}.md`
- Session ID 格式：`%Y%m%d_%H%M%S`（任务开始时生成一次）
- 详细执行规范（session_writer 调用方式、messages 填写规范等）请参考 `CLAUDE.md`
