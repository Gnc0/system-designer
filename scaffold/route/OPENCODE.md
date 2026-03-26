# 系统策划-hjj Skill (OpenCode 版本)

## 概述
本技能为系统策划多智能体工作流。**OpenCode 是 Supervisor**，读取本文件后自主决策调用哪个 Subagent。

**Subagent 调用方式（强制）**：所有 Subagent 必须使用 OpenCode 的 **Task 工具**（`subagent_type: general`）调用，读取 `prompts/` 目录下对应的 `.md` 文件作为 System Prompt 传入。**禁止**通过 `python run.py` 或任何外部脚本调用 Subagent，不得依赖 `.env` 中的 API Key。

## 与 Claude Code 版本的区别

| 特性 | Claude Code | OpenCode |
|------|-------------|----------|
| 工具名称 | Agent | Task |
| 子代理类型 | `general-purpose` | `general` |
| 配置文件 | `scaffold/route/CLAUDE.md` | `scaffold/route/OPENCODE.md` |
| 工作流 | 相同 | 相同 |

## 目录结构
```
scaffold/route/OPENCODE.md         ← OpenCode 的 Supervisor 配置（当前文件）
scaffold/route/CLAUDE.md           ← Claude Code 版本的 Supervisor 配置

prompts/
  system_designer.md               ← 系统策划 Agent 的 System Prompt（核心，受守护）
  requirements_analyzer.md         ← 需求拆解 Agent 的 System Prompt（可直接编辑）
  standards_reviewer.md            ← 规范审查 Agent 的 System Prompt（可直接编辑）
  reverse_requirements.md          ← 逆向需求 Agent 的 System Prompt（可直接编辑）
  prompt_guardian.md               ← Prompt 守护 Agent 的 System Prompt（可直接编辑）

docs/
  project_doc_index.md             ← 项目历史文档目录索引
  reference/                       ← 逆向需求流程生成的 Draft 与参考文档
  analysis/                        ← 分析报告等中间产物

data/
  test/                            ← 每次调用的传参记录（调试用，自动生成）
  images/                          ← 用户上传的参考图（自动保存）
  sessions/                        ← 完整对话记录 YAML（自动生成）

src/
  subagent/system_designer_beta/   ← LangGraph Subagent 框架
  xlsx_to_md.py                    ← 将 xlsx 策划文档转为 txt 制表符格式（读取"功能需求" Sheet）
```

---

## 核心工作流

### 一、写策划案（主流程）

**Step 1：获取 UI 参考图或文字描述**

检测到"写策划案"、"帮我设计XX系统"等意图时，按以下流程获取 UI 信息：

**方案A：用户提供 UI 参考图（优先）**
- 提示语：「请提供该功能的 UI 参考图，可直接在对话中粘贴截图或拖入图片文件。」
- 收到图片后，保存到 `data/images/{session_id}_{原始文件名或 ref.png}`
- 进入 Step 2

**方案B：用户选择文字描述（备选）**
- 如果用户说「没有参考图」或「用文字描述」，进入文字描述模式
- 提示语：「请用文字描述你想要的 UI 布局和功能，我会帮你生成 UI 参考图。」
- 用户提供文字描述后，**调用 AI 生成 UI 参考图**：
  ```
  请根据以下描述，生成一个 UI 参考图的详细文字描述（包括布局、颜色、元素位置等），以便后续策划：

  用户描述：{用户提供的文字描述}

  输出格式：
  1. 整体布局描述
  2. 主要元素及位置
  3. 颜色和风格
  4. 交互逻辑
  ```
- 将生成的 UI 描述保存到 `data/images/{session_id}_ai_generated_ui.md`
- 进入 Step 2

**Step 2：调用需求拆解 Agent（A2）**
- 使用 Task 工具（`subagent_type: general`），将 `prompts/requirements_analyzer.md` 全文作为 System Prompt，将图片描述和用户说明作为用户输入传入。
- 将输出的需求 Draft **完整展示**给用户。
- **必须等待用户明确确认**（「确认」或「修改如下：...」），不得跳过此步骤。
- 用户修改则将修改后的内容作为 confirmed_draft，必须调用 Write 工具保存该文档在 `docs/{session_id}_confirmed_draft.md`。

**Step 3：调用系统策划 Agent（A1）**
- 使用 Task 工具（`subagent_type: general`），将 `prompts/system_designer.md` 全文作为 System Prompt，将 `docs/{session_id}_confirmed_draft.md` 的地址传入。
- A1 如需查阅项目历史文档，通过 Read 工具按需读取（`docs/project_doc_index.md` 中的路径），查阅完毕后无需在输出中保留文档内容。
- A1 返回策划案地址 `docs/{session_id}_{docs_name}.md` 后，读取该策划案。

**Step 4：自动调用规范审查 Agent（A3）**
A1 输出完毕后，立即执行：
- 使用 Task 工具（`subagent_type: general`），将 `prompts/standards_reviewer.md` 全文作为 System Prompt，将A1输出的 `docs/{session_id}_{docs_name}.md` 的地址作为用户输入传入。
- 接受审查结果，将审查结果输出为「---\n## 规范审查报告」分隔块。
- **审查报告展示后，必须等待用户明确确认哪些问题需要修改**（用户可逐条确认、部分采纳或全部忽略），不得自动开始修改。
- 若用户确认有需修改项，以用户确认的问题列表为准，启动修改流程（见注意事项）；若用户表示无需修改，直接进入 Step 5。



**Step 5：调用 Prompt 守护 Agent（A5）**
- 使用 Task 工具（`subagent_type: general`），将 `prompts/prompt_guardian.md` 全文作为 System Prompt，将本次对话要点摘要作为用户输入传入。
- 若 A5 建议更新，将 diff 完整展示给用户，等待文字确认。
- **更新规则（严格执行，不可违反）**：
  - 每次只执行**一条**建议。
  - 每条建议只涉及**一句话**（原子操作：增/删/改其中之一）。
  - **严禁**建议重写段落、章节或大段内容。
  - 用户若想大幅修改，告知其自行编辑 `prompts/system_designer.md`。

---

### 二、审查策划案

当用户说「帮我审查这份策划案」时：
1. 要求用户粘贴策划案内容。
2. 直接调用 A3（跳过 A1、A2）。
3. 展示审查报告。


---

### 三、修改策划案

当用户说「修改XXX」时：
1. 将原策划案 + 修改意见合并，传给 A1。
2. A1 输出修改后版本。
3. 自动调用 A3 审查。


---

### 四、逆向需求（从策划案重生成标准格式策划案）

当用户说「逆向需求」、「从策划案还原需求」、「分析这份策划案的需求」、「重新生成策划案」等意图时：

**Step 1：获取策划案内容**
- 先读取 `docs/project_doc_index.md`，按用户提供的功能名称（如"升星系统"）模糊匹配，找到对应文档路径后：
  - 若为 `.xlsx` 文件，用 Bash 工具调用 `src/xlsx_to_md.py` 转换：
    ```bash
    python src/xlsx_to_md.py "D:/Docs/策划/系统文档/{相对路径}" docs/reference
    ```
    输出文件在 `docs/reference/{文件名}.md`，再用 Read 工具读取该文件内容作为策划案输入。
  - 若为 `.docx` / `.txt` / `.md` 文件，直接用 Read 工具读取。
- 若索引中未找到匹配项，再要求用户粘贴策划案内容（txt/md 或直接粘贴均可）。
- 从策划案标题或用户说明中提取 `feature_name`（如"成就系统"）。

**Step 2：调用 A4（逆向需求 Agent）并立即保存**
- 使用 Task 工具（`subagent_type: general`），将 `prompts/reverse_requirements.md` 全文作为 System Prompt，将用户提供的策划案文本作为用户输入传入。
- 将 A4 输出的逆向需求 Draft **完整展示**给用户（含 Part 2 逆向质量自评）。


**Step 3：自动调用 A1（system_designer）生成标准格式策划案**
- A4 输出后，**立即自动**（无需用户确认）执行此步骤。
- 取 A4 输出中 `---` 分隔线**之前的 Part 1 内容**作为 confirmed_draft（不含逆向质量自评）。
- 使用 Task 工具（`subagent_type: general`），将 `prompts/system_designer.md` 全文作为 System Prompt，将 confirmed_draft 作为用户输入传入。
- A1 如需查阅项目历史文档，通过 Read 工具按需读取（`docs/project_doc_index.md` 中的路径）。
- A1 返回策划案地址 `docs/{session_id}_{docs_name}.md` 后，读取该策划案。


**Step 4：自动调用 A3（规范审查）**
- A1 输出完毕后，立即调用 A3 审查（同主流程 Step 4）。
- 将审查报告附在策划案后展示，**等待用户确认**哪些问题需修改。



> **典型用途**：将非标准格式旧策划案重整为 system_designer 规范格式、质量评估、需求复盘。

---

## 调用规范

### Session ID
同一次任务全程使用同一个 `session_id`，格式：`%Y%m%d_%H%M%S`（任务开始时生成一次）。

### 传参规范
调用 Subagent 时，在 prompt 中附加必要的上下文（如项目名称、背景说明等），但附加内容**不得与 `prompts/` 目录下任何 System Prompt 的规则产生冲突**。

### 项目历史文档
- 目录索引：`docs/project_doc_index.md`
- A1 需要查阅项目历史文档时，在 Agent prompt 中指示其使用 Read 工具按需读取对应文件。查阅完毕后，输出中无需保留文档内容。

---

## OpenCode 特定配置

### 工具调用方式
OpenCode 使用 Task 工具调用子代理，语法如下：

```python
Task(
    description="调用需求拆解Agent",
    prompt="System Prompt内容...",
    subagent_type="general"
)
```

### 与 Claude Code 的兼容性
- 本配置文件（`scaffold/route/OPENCODE.md`）与 `scaffold/route/CLAUDE.md` 工作流完全相同
- 唯一区别是工具名称和子代理类型参数：
  - Claude Code：`Agent` 工具，`subagent_type: general-purpose`
  - OpenCode：`Task` 工具，`subagent_type: general`
- prompts/ 目录下的文件可以共用

---

## 注意事项
- **永远不要**在没有 UI 参考图或文字描述的情况下开始写策划案（至少需要其中一种）。
- **永远不要**跳过用户对需求 Draft 的确认步骤。
- **所有 Subagent 必须使用 Task 工具调用，禁止使用 python run.py 或外部脚本。**
- **所有生成的策划案必须保存一份到 `docs/` 目录，文件名格式：`{feature_name}_{session_id}.md`，不要使用md语法！！！**
- **规范审查后如有需修改内容，必须先经用户确认（以用户确认的问题列表为准，A3 报告仅供参考），将策划案保存到 `docs/` 目录（若尚未保存），然后启动 Subagent（`subagent_type: general`），在 System Prompt 中传入 `prompts/system_designer.md` 全文，指示其使用 Edit 工具直接编辑该 `.md` 文件，根据用户确认的修改项逐一修正，修改完毕后输出修改摘要。禁止由 OpenCode 主线程直接修改策划案文件。**
