# System Designer Skill

基于 Claude Code / OpenCode 的游戏系统策划多智能体工作流。给定 UI 参考图，自动完成需求拆解、策划案撰写、规范审查的全流程。

---

## 目录

- [支持工具](#支持工具)
- [工作原理](#工作原理)
- [前置要求](#前置要求)
- [安装步骤](#安装步骤)
- [配置](#配置)
- [使用方法](#使用方法)
- [目录结构](#目录结构)
- [常见问题](#常见问题)

---

## 支持工具

本项目支持两种 AI 工具：

| 工具 | 配置文件 | 工具名称 | 安装命令 |
|------|----------|----------|----------|
| **Claude Code** | `CLAUDE.md` | Agent | `npm install -g @anthropic-ai/claude-code` |
| **OpenCode** | `OPENCODE.md` | Task | `npm install -g opencode` |

> 根目录入口文件会把两种工具分别路由到 `scaffold/route/` 下的对应配置。

---

## 工作原理

```
用户（Claude Code / OpenCode 对话）
        ↓
  AI 工具（Supervisor）
   读取配置文件自主决策
        ↓
 ┌──────┬──────┬──────┬──────┐
 A2     A1     A3     A4     A5
需求   策划   规范   逆向   Prompt
拆解    案    审查   需求   守护
```

- **你只需要和 AI 工具说话**，其余 Agent 均由工具自动调用。
- Python 依赖（LangGraph）是底层框架，AI 工具通过 Agent/Task 工具直接驱动各 Agent，**无需手动运行 Python 脚本**。

---

## 前置要求

### 1. AI 工具（二选一）

#### Claude Code

```bash
# 需要先安装 Node.js 18+（https://nodejs.org）
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

#### OpenCode

```bash
# 需要先安装 Node.js 18+（https://nodejs.org）
npm install -g opencode

# 验证安装
opencode --version
```

安装完成后验证：

```bash
claude --version
```

> 如果提示 `command not found`，请确认 Node.js 已正确安装，并将 npm 全局目录加入 PATH。

---

### 2. Python

本项目需要 **Python 3.10 或以上版本**。

**检查是否已安装：**

```bash
python --version
# 或
python3 --version
```

**如未安装，按以下步骤操作：**

#### Windows

1. 前往 [https://www.python.org/downloads/](https://www.python.org/downloads/)，下载最新稳定版（3.12 推荐）。
2. 运行安装包，**务必勾选"Add Python to PATH"**，再点击 Install Now。
3. 安装完成后重新打开终端，运行 `python --version` 确认。

---

## 安装步骤

### 第一步：克隆或下载项目

```bash
# 如果使用 git
git clone <项目地址>
cd "system designer skill"

# 或直接将项目文件夹放到你喜欢的位置
```

### 第二步：安装 Python 依赖

进入 Python 包目录并安装依赖：

```bash
cd "src/subagent/system_designer_beta"

# （推荐）创建虚拟环境，避免污染全局 Python 环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

安装完成后，你会看到类似以下输出：

```
Successfully installed langgraph-x.x.x langchain-x.x.x anthropic-x.x.x ...
```

---

## 配置

### 配置 .env 文件

在 `src/subagent/system_designer_beta/` 目录下，复制示例文件并填写配置：

```bash
# 在 src/subagent/system_designer_beta/ 目录执行
cp .env.example .env
```

用文本编辑器打开 `.env`，填写以下内容：

```env
# 必填：Anthropic API Key
# 前往 https://console.anthropic.com 获取
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxx

# 项目历史文档的本地路径（如不需要查阅历史文档可不填）
PROJECT_DOC_PATH=
```

> **安全提示**：`.env` 文件包含密钥，请勿提交到 git 仓库。

---

## 使用方法

在项目根目录启动 Claude Code 后，直接用自然语言对话即可。

### 写策划案

```
帮我设计一个终身福利系统
```

Claude Code 会：

1. 要求你提供 UI 参考图（直接粘贴截图即可）
2. 调用需求拆解 Agent，输出需求 Draft 供你确认
3. 确认后调用策划 Agent 撰写完整策划案
4. 自动进行规范审查
5. 将策划案保存到 `docs/` 目录

### 审查策划案

```
帮我审查这份策划案：[粘贴策划案内容]
```

### 修改策划案

```
修改上面策划案中的奖励部分，改为...
```

### 逆向需求（从策划案重生成标准格式策划案）

```
逆向需求：公会红包
从策划案还原需求
分析这份策划案的需求
```

Claude Code 会：

1. 读取 `docs/project_doc_index.md` 查找对应文档
2. 调用逆向需求 Agent，生成标准格式需求 Draft
3. 自动调用策划 Agent 生成标准格式策划案
4. 自动进行规范审查

---

## 目录结构

```
system designer skill/
├── CLAUDE.md                          # 根目录路由入口，分流到 scaffold/route/CLAUDE.md
├── OPENCODE.md                        # 根目录路由入口，分流到 scaffold/route/OPENCODE.md
├── SKILL.md                           # Skill 描述文件
├── README.md                          # 本文件
├── agent.md                           # OPENCODE/CLAUDE 差异整理
├── scaffold/
│   └── route/
│       ├── CLAUDE.md                  # Claude Code 正式工作流配置
│       └── OPENCODE.md                # OpenCode 正式工作流配置
├── prompts/
│   ├── system_designer.md             # A1 策划 Agent 的 Prompt（受守护）
│   ├── requirements_analyzer.md       # A2 需求拆解 Agent 的 Prompt
│   ├── standards_reviewer.md          # A3 规范审查 Agent 的 Prompt
│   ├── reverse_requirements.md        # A4 逆向需求 Agent 的 Prompt
│   └── prompt_guardian.md             # A5 Prompt 守护 Agent 的 Prompt
├── docs/
│   ├── project_doc_index.md           # 项目历史文档目录索引
│   ├── analysis/                      # 分析报告等中间产物
│   └── reference/                     # 转换后的参考文档与逆向草稿
├── data/
│   ├── images/                        # 用户上传的 UI 参考图（自动保存）
│   ├── sessions/                      # 完整对话记录 YAML（自动生成）
│   └── test/                          # 调试用传参记录（自动生成）
├── src/
│   ├── xlsx_to_md.py                  # Excel 转 Markdown 工具
│   └── subagent/system_designer_beta/ # LangGraph Subagent 框架
│       ├── .env.example               # 环境变量示例
│       ├── .env                       # 你的本地配置（需自行创建）
│       ├── requirements.txt           # Python 依赖
│       ├── run.py                     # 调试入口
│       ├── config.py                  # 路径配置
│       ├── agents/                    # 各 Agent 实现
│       └── tools/                     # 工具函数

│           ├── progress.py            # 进度提示工具
│           └── ...
```

---

## 常见问题

**Q：运行 `claude` 时提示找不到命令？**
确认 Node.js 已安装且版本 ≥ 18，然后运行 `npm install -g @anthropic-ai/claude-code` 重新安装。

**Q：pip install 时报错"No module named pip"？**
运行 `python -m ensurepip --upgrade` 修复，再重试安装。

**Q：提示 ANTHROPIC_API_KEY 未设置？**
确认已在 `src/subagent/system_designer_beta/.env` 中填写了正确的 API Key，且当前终端已激活虚拟环境。

**Q：Claude Code 没有按照预期流程执行？**
确认是在项目根目录下运行 `claude`，这样根目录 `CLAUDE.md` 才会被自动加载，并继续路由到 `scaffold/route/CLAUDE.md`。

**Q：能否直接运行 run.py？**
`run.py` 仅用于调试单个 Agent，正常使用请通过 Claude Code 对话驱动，不要直接调用 Python 脚本。

**Q：逆向需求功能什么时候用？**
当你有旧策划案（Excel/Word/Markdown 格式），想要重整为标准格式策划案时使用。系统会自动从 `docs/project_doc_index.md` 中查找对应文档。

**Q：PROJECT_DOC_PATH 如何配置？**
在 `.env` 文件中设置为你项目文档的本地路径，例如：`PROJECT_DOC_PATH=D:\Docs\策划\系统文档`。如果不配置，逆向需求功能将无法查阅历史文档。
