# 系统策划-hzw Skill

## 概述
本技能为系统策划多智能体工作流。**Claude Code 是 Supervisor**，读取本文件后自主决策调用哪个 Subagent。

**Subagent 调用方式（强制）**：所有 Subagent 必须使用 Claude Code 的 **Agent 工具**（`subagent_type: general-purpose`）调用，读取 `prompts/` 目录下对应的 `.md` 文件作为 System Prompt 传入。**禁止**通过 `python run.py` 或任何外部脚本调用 Subagent，不得依赖 `.env` 中的 API Key。

## 目录结构
```
prompts/system_designer.md        ← 系统策划 Agent 的 System Prompt（核心，受守护）
prompts/requirements_analyzer.md  ← 需求拆解 Agent 的 System Prompt（可直接编辑）
prompts/standards_reviewer.md     ← 规范审查 Agent 的 System Prompt（可直接编辑）
prompts/reverse_requirements.md   ← 逆向需求 Agent 的 System Prompt（可直接编辑）
docs/project_doc_index.md         ← 项目历史文档目录索引
data/test/                        ← 每次调用的传参记录（调试用，自动生成）
data/images/                      ← 用户上传的参考图（自动保存）
data/sessions/                    ← 完整对话记录 YAML（自动生成）
src/subagent/system_designer_beta/ ← LangGraph Subagent 框架
src/xlsx_to_md.py                 ← 将 xlsx 策划文档转为 txt 制表符格式（读取"功能需求" Sheet）
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
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/requirements_analyzer.md` 全文作为 System Prompt，将图片描述和用户说明作为用户输入传入。
- 将输出的需求 Draft **完整展示**给用户。
- **必须等待用户明确确认**（「确认」或「修改如下：...」），不得跳过此步骤。
- 用户修改则将修改后的内容作为 confirmed_draft。

**Step 3：调用系统策划 Agent（A1）**
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/system_designer.md` 全文作为 System Prompt，将 confirmed_draft 作为用户输入传入。
- A1 如需查阅项目历史文档，通过 Read 工具按需读取（`docs/project_doc_index.md` 中的路径），查阅完毕后无需在输出中保留文档内容。
- 输出：完整策划案文档。

**Step 4：自动调用规范审查 Agent（A3）**
A1 输出完毕后，立即执行：
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/standards_reviewer.md` 全文作为 System Prompt，将 A1 输出的策划案作为用户输入传入。
- 将审查结果附在策划案后，一起展示给用户。
- 格式：先输出策划案，再输出「---\n## 规范审查报告」分隔块。
- **审查报告展示后，必须等待用户明确确认哪些问题需要修改**（用户可逐条确认、部分采纳或全部忽略），不得自动开始修改。
- 若用户确认有需修改项，以用户确认的问题列表为准，启动修改流程（见注意事项）；若用户表示无需修改，直接进入 Step 5。

**Step 5：保存对话记录**
**不得**直接用 Write 工具手写 YAML，必须通过 `session_writer.py` 保存，流程如下：

1. **必须用 Python `json.dump()` 生成 JSON 文件**（不得用 Write 工具直接写 JSON 文本，中文引号会导致 `JSONDecodeError`）：

```bash
python -c "
import json
data = {
  'session_id': '20240101_120000',
  'feature_name': 'XX系统',
  'workflow': 'write',
  'image_paths': ['data/images/...'],
  'requirements_draft': '''（A2 输出的完整原文，一字不差，不得摘要）''',
  'confirmed_draft': '''（用户确认/修改后的完整原文）''',
  'planning_document': open('docs/XX系统_20240101_120000.md', encoding='utf-8').read(),
  'planning_document_path': 'docs/XX系统_20240101_120000.md',
  'review_result': '''（A3 输出的完整审查报告原文）''',
  'messages': [
    {'role': 'user', 'content': '''（第1条用户消息完整原文，一字不差）'''},
    {'role': 'assistant', 'content': '''（A2 需求 Draft 完整原文）'''},
    {'role': 'user', 'content': '''（用户确认/修改意见完整原文）'''},
    {'role': 'assistant', 'content': '''（A1 策划案完整原文 + ---\n规范审查报告\n + A3 审查完整原文）'''}
  ]
}
with open('data/sessions/.tmp_20240101_120000.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('JSON written OK')
"
```

如果字段内容较长，先把文本保存到文件再用 `open().read()` 读入，避免 Python 单行命令过长。

**messages 填写规范（严格执行）**：
- 每条 `content` 必须是该轮对话的**实际完整内容**，不得用描述性摘要（如「调用A2...」「输出策划案...」）代替。
- assistant 轮中，如果展示给用户的内容很长，必须完整复制，不得截断。
- 修改轮次 message 额外加 `"type": "revision"`。

2. 用 Bash 工具调用 session_writer（**必须设置 `PYTHONIOENCODING=utf-8`**，否则 Windows GBK 终端会因 ✅ emoji 报 `UnicodeEncodeError`）：
```bash
cd "d:/Docs/design/cc/system designer skill" && PYTHONIOENCODING=utf-8 python "src/subagent/system_designer_beta/tools/session_writer.py" --input "data/sessions/.tmp_{session_id}.json"
```

3. 确认输出含 `Session 已保存` 后，删除临时 JSON 文件。

**字段规则**：
- 所有文本字段必须是对应 Agent 的**完整输出原文**，禁止任何摘要、截断或占位符（如 `[A2输出...]`）。
- `messages` 每条的 `content` 是该轮的实际发言全文，修改轮次额外加 `"type": "revision"`。
- `workflow` 固定填 `"write"` / `"review"` / `"revision"` / `"reverse"` / `"reverse_only"` 之一。
- 审查流程（workflow=review）：`requirements_draft` 和 `confirmed_draft` 填空字符串 `""`。
- 逆向流程（workflow=reverse）：`requirements_draft` = A4 Part 1 原文，`confirmed_draft` = 传给 A1 的内容（与 requirements_draft 相同），`image_paths` = `[]`。

**Step 6：调用 Prompt 守护 Agent（A5）**
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
1. 要求用户粘贴策划案内容。
2. 直接调用 A3（跳过 A1、A2）。
3. 展示审查报告。
4. 保存对话到 `data/sessions/{session_id}.yaml`，同样走 session_writer：
   - `workflow: "review"`，`planning_document` = 用户提供的策划案完整原文，`review_result` = A3 完整原文，`requirements_draft`/`confirmed_draft` = `""`

---

### 三、修改策划案

当用户说「修改XXX」时：
1. 将原策划案 + 修改意见合并，传给 A1。
2. A1 输出修改后版本。
3. 自动调用 A3 审查。
4. 保存 YAML，同样走 session_writer：
   - `workflow: "revision"`，`planning_document` = A1 修改后完整原文，`review_result` = A3 完整原文，修改轮次 message 加 `"type": "revision"`

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
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/reverse_requirements.md` 全文作为 System Prompt，将用户提供的策划案文本作为用户输入传入。
- 将 A4 输出的逆向需求 Draft **完整展示**给用户（含 Part 2 逆向质量自评）。
- **A4 输出后立即**用 Write 工具将 Part 1 完整原文（`---` 分隔线之前的内容，不含逆向质量自评）保存到 `docs/reference/{feature_name}_{session_id}_draft.md`。

**Step 3：自动调用 A1（system_designer）生成标准格式策划案**
- A4 输出后，**立即自动**（无需用户确认）执行此步骤。
- 取 A4 输出中 `---` 分隔线**之前的 Part 1 内容**作为 confirmed_draft（不含逆向质量自评）。
- 使用 Agent 工具（`subagent_type: general-purpose`），将 `prompts/system_designer.md` 全文作为 System Prompt，将 confirmed_draft 作为用户输入传入。
- A1 如需查阅项目历史文档，通过 Read 工具按需读取（`docs/project_doc_index.md` 中的路径）。
- **立即将 A1 输出的策划案保存到 `docs/{feature_name}_{session_id}.md`**（不要使用 md 语法！），然后展示给用户。

**Step 4：自动调用 A3（规范审查）**
- A1 输出完毕后，立即调用 A3 审查（同主流程 Step 4）。
- 将审查报告附在策划案后展示，**等待用户确认**哪些问题需修改。

**Step 5：保存对话记录**
- 同主流程 Step 5，通过 `session_writer.py` 保存 YAML，字段说明：
  - `workflow: "reverse"`
  - `requirements_draft` = A4 输出的 Part 1 完整原文
  - `confirmed_draft` = 传给 A1 的 Part 1 内容（与 requirements_draft 相同）
  - `planning_document` = A1 输出的完整策划案全文
  - `planning_document_path` = `docs/{feature_name}_{session_id}.md`
  - `review_result` = A3 输出的完整审查报告原文
  - `image_paths` = `[]`（逆向流程无参考图）

> **典型用途**：将非标准格式旧策划案重整为 system_designer 规范格式、质量评估、需求复盘。

---

## 调用规范

### Session ID
同一次任务全程使用同一个 `session_id`，格式：`%Y%m%d_%H%M%S`（任务开始时生成一次）。

### 传参规范
调用 Subagent 时，在 prompt 中附加必要的上下文（如项目名称、背景说明等），但附加内容**不得与 `prompts/` 目录下任何 System Prompt 的规则产生冲突**。

### 项目历史文档
- 目录索引：`docs/project_doc_index.md`
- A1 需要查阅历史文档时，在 Agent prompt 中指示其使用 Read 工具按需读取对应文件。查阅完毕后，输出中无需保留文档内容。

---

## 注意事项
- **永远不要**在没有 UI 参考图或文字描述的情况下开始写策划案（至少需要其中一种）。
- **永远不要**跳过用户对需求 Draft 的确认步骤。
- **所有 Subagent 必须使用 Agent 工具调用，禁止使用 python run.py 或外部脚本。**
- **所有生成的策划案必须保存一份到 `docs/` 目录，文件名格式：`{feature_name}_{session_id}.md`，不要使用md语法！！！**
- **规范审查后如有需修改内容，必须先经用户确认（以用户确认的问题列表为准，A3 报告仅供参考），将策划案保存到 `docs/` 目录（若尚未保存），然后启动 Subagent（`subagent_type: general-purpose`），在 System Prompt 中传入 `prompts/system_designer.md` 全文，指示其使用 Edit 工具直接编辑该 `.md` 文件，根据用户确认的修改项逐一修正，修改完毕后输出修改摘要。禁止由 Claude Code 主线程直接修改策划案文件。**
