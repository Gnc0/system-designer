# System Designer Harness - v0_dev

游戏系统与数值策划的多智能体协作规范。基于 pi 的 agents 机制，按能力层级将策划工作拆分为专业 Agent，Agent 之间通过「设计合同（contract）」逐级传递设计责任，主线程负责调度与用户确认。

## 会话开始（每次会话必做）

1. **读取记忆**：读取 `docs/memory.md`，了解历史任务的成功/失败经验，避免重复踩坑。
2. **生成 session_id**：主线程运行 `date +%Y%m%d_%H%M%S` 生成本次会话的 session_id，贯穿本次会话所有阶段（模块 → 系统 → 文档 → 数值）不变；任务目录命名同时使用其派生形式（见「输出约定」）。
3. **superpowers 安装提示（一次性）**：若用户尚未安装 superpowers，且当前 harness 不是 codex 或 claude code，则向用户建议安装 superpowers——推荐理由：它提供 brainstorming、test-driven-development、systematic-debugging、verification-before-completion 等经过验证的通用工程工作流技能，可补齐本仓库未覆盖的通用研发环节。**若用户拒绝安装，立即将本条提示从 AGENTS.md 中删除，之后不再提示。**

## 术语

| 术语 | 含义 |
|------|------|
| 策划案 | 系统策划文档，描述游戏内功能系统的完整设计 |
| 需求 Draft | 从用户输入提取的结构化设计草案（模块循环分析 / 体验行为拆解 / 数值拆解） |
| 设计合同 | 上游向下游传递的必要设计责任，包含：归属者/来源、状态、适用域、义务、对上保证/验收、冲突返回。下文简称 contract |
| session_id | 本次会话的唯一标识，格式 `%Y%m%d_%H%M%S`，会话开始时由主线程运行脚本生成 |

## Agent 体系

| Agent | 层级定位 | 职责 | 定义文件 |
|-------|----------|------|----------|
| `sd-module-loop` | 高级系统策划 | 模块循环分析：定义模块目标、系统职责、跨系统流转与模块循环，向单系统下发约束 | `agents/sd-module-loop.md` |
| `sd-mda` | 中级系统策划 | 单系统 MDA 拆解：体验目标、玩家行为闭环、规则设计要点 | `agents/sd-mda.md` |
| `sd-writer` | 初级系统策划 | 继承已确认结论，落地为结构化、可实现、可测试的策划文档 | `agents/sd-writer.md` |
| `nd-mda` | 数值需求拆解 | 数值目标、数值循环（产出—消耗—验证）、公式框架与锚点约束 | `agents/nd-mda.md` |
| `nd-writer` | 数值细案写作 | 调查实际代码与表结构，推导参数并产出可复核、可落表的数值细案 | `agents/nd-writer.md` |
| `design-purpose-reviewer` | 设计目的审查 | 基于「直面设计」论证结构审查设计目的；不替用户生成正式目的，也不审查完整机制/规则文档 | `agents/design-purpose-reviewer.md` |

`docs/system-designer-level-spec.md` 是系统策划线（`sd-module-loop` / `sd-mda` / `sd-writer`）共用的能力层级标尺（初级/中级/高级/资深），不作为 Agent 调用。

**固定管线**：模块 → 系统 → 文档 固定为 `sd-module-loop → sd-mda → sd-writer`，不得跳步；数值线为 `nd-mda → nd-writer`。

## 参考文档

| 文档 | 用途 |
|------|------|
| `docs/qpdi/qpdi.md` | QPDI 认知与论证框架：Q/P/D/I 静态结构、Structural Locality、Discover 与 SCCO |
| `docs/qpdi/qpdi-compose.md` | 编写 QPDI 的 Q 与逐层展开 D，从用户原话/既有材料中保全论证 |
| `docs/qpdi/qpdi-tribunal.md` | SCCO 公检法审查：challenger & prover → counter → judge 对抗式审查，按 Sound/Complete/Concise/Optimization 四维收敛 |
| `docs/my-taste.md` | 设计品味：纠错后重建评价系统 |

`design-purpose-reviewer` 的「直面设计」论证结构与 QPDI 框架同源，上述文档可作为其方法参考；需要对抗式审查任意产物时可参考 `qpdi-tribunal.md`。

## 约束

1. **永远不要**跳过用户确认：模块结论、单系统拆解、数值方案均需用户确认后才能进入下游
2. **永远不要**跳过管线阶段：不得从模块分析直接跳到策划案，不得让 `sd-writer` 补造未经 `sd-mda` 设计或确认的单系统结论
3. **所有子代理通过 agent 名称直接调用**（sd-writer / sd-mda / sd-module-loop / nd-mda / nd-writer / design-purpose-reviewer），禁止 read prompt 文件再传入
4. **`task` 参数只包含用户数据与必要上下文**，禁止附加与 agent system prompt 冲突的指令
5. **所有派遣的 subagent 必须先读取本文件**：主线程传给 subagent 的每条消息开头必须包含「请先读取项目根目录的 AGENTS.md 再开始任务。」
6. **调度权归主线程**：子代理不得自行派遣下游 Agent；需要下游接续时，在输出中给出下游派遣建议（接收方、目标、义务、验收），由主线程在用户确认后按管线派遣
7. **所有生成的策划案必须保存到 `docs/` 目录**，文件名包含 session_id；任务过程中的 Draft、审查报告、待确认项、临时文件等过程产物保存在本次任务目录（见「输出约定」）
8. **修改策划案文件**：必须先经用户确认修改项，再由子代理用 `edit` 工具编辑，禁止主线程直接修改
9. **最小化修改原则**：修改本文件时最小化修改，不要全量优化

## 子代理调用

- 使用 `subagent` 工具的 SINGLE 模式调用
- system prompt 由 pi 框架自动注入（`~/.pi/agent/agents/*.md`）
- 每条 task 消息开头固定加入：「请先读取项目根目录的 AGENTS.md 再开始任务。」
- 传递上游结论时，主线程按 contract 六要素整理（归属者/状态、适用域、义务、对上保证/验收、冲突返回），不整份粘贴上游 Draft 原文；未确认项保留状态标签，不得默认升级为已确认

---

# 工作流

## 一、模块设计 → 策划案（主流程）

**Step 1：模块循环分析（sd-module-loop）**

```
subagent SINGLE: { agent: "sd-module-loop", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n{用户的模块构想 / 已有系统清单 / 运行问题}" }
```

→ 展示模块循环分析 Draft（模块定位、系统职责、跨系统流转、下游设计合同）→ **等待用户确认模块结论**
→ Draft 与用户反馈存入本次任务目录

若用户只要模块分析，下发设计合同后即停止，不擅自进入下游。

**Step 2：单系统体验与行为拆解（sd-mda，逐系统）**

```
subagent SINGLE: { agent: "sd-mda", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n以下是模块设计合同（按六要素整理）：\n\n{归属者/状态}\n{适用域}\n{义务}\n{对上保证/验收}\n{冲突返回}\n\n请分析系统：{系统名}\n\n{用户补充说明}" }
```

→ 展示 Draft（体验目标、玩家行为闭环、规则设计要点）→ **等待用户确认**

**Step 3：策划案撰写（sd-writer）**

```
subagent SINGLE: { agent: "sd-writer", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n请根据以下已确认的系统设计合同撰写策划案。\n\n{已确认的 sd-mda 结论，按六要素整理}\n\nsession_id: {session_id}\n\n保存路径：docs/{session_id}_{文档名}.txt\n\n最后将文件保存为txt文件。" }
```

→ sd-writer 返回的规则草稿与设计问题清单，由主线程备注记录到本次任务目录；涉及上游裁决的设计问题回流 `sd-module-loop` / `sd-mda` 或交用户确认后，再产出正式策划案

## 二、单系统设计（无模块上游）

用户直接提出单个系统需求时：`sd-mda` → 用户确认 → `sd-writer`，调用方式同主流程 Step 2、Step 3。

## 三、数值设计

前提：系统方案（体验目标与规则）已确认。

**Step 1：数值需求拆解（nd-mda）**

```
subagent SINGLE: { agent: "nd-mda", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n以下是系统规则与体验目标（按合同六要素整理）：\n\n{已确认的系统方案}\n\n{用户补充说明}" }
```

→ 展示数值目标、数值循环与公式框架 → **等待用户确认**

**Step 2：数值细案写作（nd-writer）**

```
subagent SINGLE: { agent: "nd-writer", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n以下是已确认的数值目标与数值结构：\n\n{已确认的 nd-mda 结论}\n\n{用户补充说明}" }
```

→ 展示数值细案与配置规格 → **等待用户确认** → 细案与配置规格存入本次任务目录

## 四、设计目的审查

```
subagent SINGLE: { agent: "design-purpose-reviewer", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n{待审查的设计目的及相关材料}" }
```

→ 展示审查报告 → **等待用户确认后续修改** → 审查报告存入本次任务目录

只审查设计目的论证是否第一性、体系化、可验证；不生成正式目的，不审查完整机制、规则文档或模块循环。

## 五、修改策划案

```
subagent SINGLE: { agent: "sd-writer", task: "请先读取项目根目录的 AGENTS.md 再开始任务。\n\n请修改策划案 docs/{session_id}_{docs_name}.txt，修改要求：\n\n{用户修改意见}\n\n请使用 edit 工具直接编辑该文件，逐一修正后输出修改摘要。" }
```

修改完成后按需调用 `design-purpose-reviewer` 复审（仅复审修改涉及的设计目的论证，不委托完整规则审查）。

---

# 输出约定

## 任务目录

- 会话开始并生成 session_id 后，在 `docs/task/` 下创建本次任务目录：`docs/task/{yymmdd-hhmm}-{session_id前4位}/`（如 `docs/task/250927-1305-2025/`）
- 任务过程中的 Draft、规则草稿、设计问题清单、审查报告、待确认项及各类临时文件都保存在该目录，保证工程整洁；正式策划案除外（见下）

## 正式交付物

- **sd-writer 正式策划案**：txt 内容，标题层级「一、/ 1.1 / 1.1.1 / 1）」，多用 tab 缩进与换行，便于复制到 Excel；正式案只包含已确认规则，未确认设计问题保留在草稿与待确认清单
- **文档命名**：`docs/{session_id}_{文档名}.txt`

## Draft 信息标注

- 各 Draft（模块 / 体验行为 / 数值）：已知、推测、条件必要、需确认、可后置必须区分标注，不得把推测写成确定结论

## 记忆（memory.md）

- `docs/memory.md` 记录历史任务的概述与成功/失败经验，会话开始时默认读取
- 每完成一次任务，主线程在 `docs/memory.md` 追加一条记录（日期、任务概述、结果、经验教训）
- 记录上限 50 条；达到 50 条后必须询问用户是否将旧记录归档到 `docs/memory/` 目录
