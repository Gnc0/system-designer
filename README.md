# System Designer Harness - v0_dev

游戏系统策划多智能体工作流。基于 pi 的 agents 机制，将系统策划工作按能力层级拆分为多个专业 Agent，覆盖模块循环分析、单系统体验拆解、策划案撰写、数值拆解与数值细案、设计目的审查的全流程。

本项目基于 pi 构建。

## Agent 体系

系统策划按能力层级分为三级，另有独立的数值线与设计目的审查：

```
资深系统策划（全局，暂未建 Agent）
    ↓ 模块优先级 / 全局资源裁决
sd-module-loop（高级：模块循环分析）
    ↓ 模块约束 / 设计合同
sd-mda（中级：单系统体验与行为拆解）
    ↓ 已确认的体验、行为与设计要点
sd-writer（初级：策划文档落地）
```

| Agent | 层级定位 | 职责 | 定义文件 |
|-------|----------|------|----------|
| `sd-module-loop` | 高级系统策划 | 分析/设计由多个系统组成的模块：定义系统职责、跨系统流转与模块循环，向单系统下发约束 | `agents/sd-module-loop.md` |
| `sd-mda` | 中级系统策划 | 单系统 MDA 拆解：体验目标、玩家行为闭环、规则设计要点 | `agents/sd-mda.md` |
| `sd-writer` | 初级系统策划 | 将已确认的系统方案落地为结构化、可实现、可测试的策划文档 | `agents/sd-writer.md` |
| `nd-mda` | 数值需求拆解 | 将体验目标与系统规则拆解为数值目标、数值循环与公式框架 | `agents/nd-mda.md` |
| `nd-writer` | 数值细案写作 | 承接数值目标与结构，调查实际代码与配置表结构，推导参数并产出可复核、可落表的数值细案 | `agents/nd-writer.md` |
| `design-purpose-reviewer` | 设计目的审查 | 基于「直面设计」的论证结构，审查设计目的是否真正充当设计理由，是否第一性、体系化、可验证 | `agents/design-purpose-reviewer.md` |

各 Agent 之间的协作通过「上游设计合同（contract）」传递：上游结论必须说明来源、确认状态、适用域与验收条件，下游才能作为设计依据。

`docs/system-designer-level-spec.md` 不是 Agent，而是系统策划线（`sd-module-loop` / `sd-mda` / `sd-writer`）共用的能力标尺：定义初级 / 中级 / 高级 / 资深系统策划的能力边界，供各 Agent 自查责任范围、判断产出是否越界。

## 典型工作流

**模块 → 系统 → 策划案**（固定顺序，不可跳步）：

```
sd-module-loop → sd-mda → sd-writer
```

1. `sd-module-loop`：输出模块目标、系统职责、跨系统流转与下游设计合同
2. `sd-mda`：在模块约束下，确认单系统体验目标、关键行为与设计要点
3. `sd-writer`：继承已确认结论，撰写正式策划案，保存到 `docs/`

**数值线**：系统方案确认后，`nd-mda` 拆解数值目标与循环，`nd-writer` 完成参数推导与配置规格。

**审查**：`design-purpose-reviewer` 独立审查设计目的论证，不替用户生成正式目的，也不审查完整机制文档。

## 目录结构

```
system-designer/
├── AGENTS.md                             ← 业务规则 + 工作流（主线程调度约定）
├── README.md                             ← 本文件
├── agents/
│   ├── sd-module-loop.md                 ← 高级：模块循环分析 Agent
│   ├── sd-mda.md                         ← 中级：单系统体验与行为拆解 Agent
│   ├── sd-writer.md                      ← 初级：策划文档写作 Agent
│   ├── nd-mda.md                         ← 数值需求 MDA 拆解 Agent
│   ├── nd-writer.md                      ← 数值细案写作 Agent
│   ├── design-purpose-reviewer.md        ← 设计目的审查 Agent
│   └── history-bak/                      ← 历史版本归档（sd-reviewer 等）
├── docs/                                 ← 策划案输出与知识沉淀
│   ├── memory.md                         ← 任务经验记录（会话开始时读取，上限 50 条）
│   ├── memory/                           ← memory.md 历史记录归档
│   ├── my-taste.md                       ← 设计品味文档
│   ├── system-designer-level-spec.md     ← 系统策划能力层级标尺（系统策划线共用）
│   ├── project/                          ← 用户项目知识文档
│   └── task/                             ← 每次任务的详情与临时文件
├── data/                                 ← 图片、对话记录
└── src/xlsx_to_md.py                     ← Excel 转换工具
```

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/your-username/system-designer.git
cd system-designer
```

### 2. 注册 Agent 定义

将 6 个 Agent 文件软链到 pi 的 agents 目录：

```bash
# Linux / macOS
mkdir -p ~/.pi/agent/agents
for f in sd-module-loop sd-mda sd-writer nd-mda nd-writer design-purpose-reviewer; do
  ln -sf "$(pwd)/agents/$f.md" ~/.pi/agent/agents/$f.md
done

# Windows（管理员 CMD，在项目根目录执行）
mklink "%USERPROFILE%\.pi\agent\agents\sd-module-loop.md" "%cd%\agents\sd-module-loop.md"
mklink "%USERPROFILE%\.pi\agent\agents\sd-mda.md" "%cd%\agents\sd-mda.md"
mklink "%USERPROFILE%\.pi\agent\agents\sd-writer.md" "%cd%\agents\sd-writer.md"
mklink "%USERPROFILE%\.pi\agent\agents\nd-mda.md" "%cd%\agents\nd-mda.md"
mklink "%USERPROFILE%\.pi\agent\agents\nd-writer.md" "%cd%\agents\nd-writer.md"
mklink "%USERPROFILE%\.pi\agent\agents\design-purpose-reviewer.md" "%cd%\agents\design-purpose-reviewer.md"
```

验证：`subagent { action: "list" }` 应看到上述 6 个 Agent。

### 3. 在 pi 中使用

注册 Agent 后即可在 pi 中通过 `subagent` 调用；主线程按 `AGENTS.md` 的工作流约定调度（模块循环分析 / 单系统设计 / 数值设计 / 设计目的审查）。

## 使用示例

```
用户：设计一个商城模块
pi：[调用 sd-module-loop] → 输出模块目标、系统职责与跨系统流转，下发设计合同
    → [调用 sd-mda] 在模块约束下拆解充值系统：体验目标、玩家行为闭环、设计要点
    → 需求 Draft 已生成，请确认：...
用户：确认
pi：[调用 sd-writer] 撰写正式策划案 → docs/{session_id}_充值系统.md

用户：基于这个系统出数值方案
pi：[调用 nd-mda] 拆解数值目标、产出—消耗—验证循环与公式框架
    → [调用 nd-writer] 调查配置表现状 → 产出参数推导与配置规格
```

## FAQ

**Q：没有 UI 参考图能用吗？**
A：可以。直接用文字描述功能想法或粘贴参考策划案即可开始。当前各 Agent 均为文本协作，模型自带的视觉能力可直接读取对话中的截图。

**Q：可以自定义策划案格式吗？**
A：修改 `agents/sd-writer.md` 的规范部分。

**Q：只想要模块分析，不写策划案？**
A：直接触发 `sd-module-loop`，它会在下发设计合同后停止，不擅自继续下游阶段。

**Q：想调整某个层级的能力边界？**
A：参考 `docs/system-designer-level-spec.md` 的层级定义，修改对应 Agent 的定义文件。

## License

MIT

---

本项目基于 [pi](https://github.com/mariozechner/pi) 构建。
