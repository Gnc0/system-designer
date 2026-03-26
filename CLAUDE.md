# Route Loader

本文件是根目录入口，不承载具体工作流规则。

## 路由规则
- 如果当前运行环境是 Claude Code，立即加载并严格遵循 `scaffold/route/CLAUDE.md`
- 如果当前运行环境是 OpenCode，立即加载并严格遵循 `scaffold/route/OPENCODE.md`

## 执行要求
- `scaffold/route/` 下的对应文件是唯一权威版本
- 本文件只负责分流，不替代 route 目录中的正式配置
- 如本文件与 route 目录中的配置有冲突，以 route 目录中的对应文件为准
- 加载后，从上下文中卸载掉本文件，后续只遵循`scaffold/route/` 的文件