# 系统策划-hzw Skill

## 概述
本技能为系统策划多智能体工作流。**Claude Code 是 Supervisor**，读取本文件后自主决策调用哪个 Subagent。

**Subagent 调用方式（强制）**：所有 Subagent 必须使用 Claude Code 的 **Agent 工具**（`subagent_type: general-purpose`）调用，读取 `prompts/` 目录下对应的 `.md` 文件作为 System Prompt 传入。**禁止**通过 `python run.py` 或任何外部脚本调用 Subagent，不得依赖 `.env` 中的 API Key。所有的subagent调用后必须输出一下消耗的token数量。

## 目录结构
```
prompts/system_designer.md        ← 系统策划 Agent 的 System Prompt（核心，受守护）
prompts/requirements_analyzer.md  ← 需求拆解 Agent 的 System Prompt（可直接编辑）
prompts/standards_reviewer.md     ← 规范审查 Agent 的 System Prompt（可直接编辑）
docs                              ← 历史策划案
data/test/                        ← 每次调用的传参记录（调试用，自动生成）
data/images/                      ← 用户上传的参考图（自动保存）
data/sessions/                    ← 完整对话记录 YAML（自动生成）
src/subagent/system_designer_beta/ ← LangGraph Subagent 框架
```

---

## 核心工作流

### 一、写策划案（主流程）

**Step 1：索取 UI 参考图（必须，不可跳过）**
- 检测到"写策划案"、"帮我设计XX系统"等意图时，立刻要求用户提供 UI 参考图。
- 提示语：「请提供该功能的 UI 参考图，可直接在对话中粘贴截图或拖入图片文件。」
- 用户不提供则不继续，耐心等待。
- 收到图片后，将其保存到 `data/images/{session_id}_{原始文件名或 ref.png}`。

**Step 2：调用需求拆解 Agent（A2）**
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/requirements_analyzer.md` 全文作为 System Prompt，将图片描述和用户说明作为用户输入传入。
- 将输出的需求 Draft **完整展示**给用户。
- **必须等待用户明确确认**（「确认」或「修改如下：...」），不得跳过此步骤。
- 用户修改则将修改后的内容作为 confirmed_draft。

**Step 3：调用系统策划 Agent（A1）**
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/system_designer.md` 全文作为 System Prompt，将 confirmed_draft 作为用户输入传入。
- 如果 A1 需要查阅项目策划文档，可通过 `.env` 中配置的 `PROJECT_DOC_PATH` 路径按需读取。
- 输出：完整策划案文档。

**Step 4：自动调用规范审查 Agent（A3）**
A1 输出完毕后，立即执行：
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/standards_reviewer.md` 全文作为 System Prompt，将策划案内容作为用户输入传入。
- **审查输出要求**：A3 直接输出审查结果，严禁在输出中复述或引用策划案原文。
- 将审查结果附在策划案后，一起展示给用户。
- 格式：先输出策划案，再输出「---\n## 规范审查报告」分隔块。

**Step 5：保存对话记录**
将本次完整对话保存到 `data/sessions/{session_id}.yaml`，格式如下：
```yaml
session_id: "20240101_120000"
feature_name: "XX系统"
image_paths:
  - "data/images/..."
requirements_draft: "..."
confirmed_draft: "..."
planning_document: "..."
review_result: "..."
messages:
  - role: user
    content: "..."
  - role: assistant
    content: "..."
```

**Step 6：调用 Prompt 审查 Agent（A5）**
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/prompt_guardian.md` 全文作为 System Prompt，将本次对话要点摘要作为用户输入传入。
- 若 A5 建议更新，将 diff 完整展示给用户，等待文字确认。
- **更新规则（严格执行，不可违反）**：
  - 每次只执行**一条**建议。
  - 每条建议只涉及**一句话**（原子操作：增/删/改其中之一）。
  - **严禁**建议重写段落、章节或大段内容。
  - 用户若想大幅修改，告知其自行编辑 `prompts/system_designer.md`。

---

### 二、审查策划案

当用户说「帮我审查这份策划案」时：
1. 要求用户粘贴策划案内容或提供文件路径。
2. 直接调用 A3（跳过 A1、A2），将策划案内容作为用户输入传入。
3. A3 直接输出审查报告（严禁复述策划案内容）。
4. 展示审查报告。
5. 保存对话到 `data/sessions/{session_id}.yaml`。

---

### 三、修改策划案

当用户说「修改XXX」时：
1. 将原策划案 + 修改意见合并，传给 A1。
2. A1 输出修改后版本。
3. 自动调用 A3 审查。
4. 保存 YAML（在 `messages` 中标注 `type: revision`）。

---

## 调用规范

### Session ID
同一次任务全程使用同一个 `session_id`，格式：`%Y%m%d_%H%M%S`（任务开始时生成一次）。

### 传参规范
调用 Subagent 时，在 prompt 中附加必要的上下文（如项目名称、背景说明等），但附加内容**不得与 `prompts/` 目录下任何 System Prompt 的规则产生冲突**。

---

## 注意事项
- **永远不要**在没有 UI 参考图的情况下开始写策划案。
- **永远不要**跳过用户对需求 Draft 的确认步骤。
- **所有 Subagent 必须使用 Agent 工具调用，禁止使用 python run.py 或外部脚本。**
- **所有生成的策划案必须保存一份到 `docs/` 目录，文件名格式：`{feature_name}_{session_id}.txt`，不要使用md语法！！！**
- **规范审查后如有需修改内容，若修改篇幅不大，直接在 Claude Code 主线程修改，不调用 Subagent。**
