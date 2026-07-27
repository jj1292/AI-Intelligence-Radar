# 从 AI Pulse 到 AI Intelligence Radar

AI Intelligence Radar 源于一个 Dify AI 日报 Demo，但它们不是两个并列产品。AI Pulse 现在是 Radar Agent 的日报输出格式。

## 演进路线

| 阶段 | 解决的问题 | 主要局限 |
| --- | --- | --- |
| v0.1 AI Pulse | 将新闻输入筛选、排序并渲染成日报 | 只是一条独立 Demo 管道，缺少真实采集、状态和评测 |
| v0.2 Radar | 引入来源分级、统一 Signal Schema、知识卡片和趋势雷达 | 仍是确定性管道，过程状态不可观察 |
| v0.3 Eval First | 建立案例、评分规则和严格门禁 | 暴露出 48 小时时效缺口 |
| v0.4 Agent Harness | 加入真实 Atom 采集、RunState、Tool Registry、Loop 和 JSONL Trace | Planner 仍是确定性的，恢复能力尚未完成 |

## 当前产品关系

```text
一手来源
   ↓
Radar Agent：采集 → 时效/去重 → 证据门 → 状态与 Trace
   ↓
知识卡片 + 趋势雷达 + AI Pulse 日报
```

AI Pulse 不再维护独立新闻数据结构。日报直接使用 `Intelligence Signal`，因此它与知识卡片、趋势报告共享同一批来源、时效和证据边界。

## 旧材料如何保留

旧根目录说明、提示词、微信设想、日报样例和 v0.1 独立脚本已从当前工作树移除，避免访客误以为仓库包含两个产品。它们仍保留在 Git 历史中；v0.1 的主要整理提交是 `4fddc48`。

仍有价值的能力已经迁移：

- 日报渲染：`reporters/daily_briefing.py`；
- Dify 方案：`docs/adapters/dify.md`；
- 标准信号输入：`schemas/intelligence-signal.schema.json`；
- 日报运行步骤：Agent Loop 中的 `write_briefing` 工具。

## 架构决策

- 唯一项目品牌是 **AI Intelligence Radar**。
- **AI Pulse** 只代表每日简报输出。
- 自研 Agent Harness 是学习状态、工具、记忆、评测和恢复机制的主线。
- Dify、OpenAI Agents SDK 和 LangGraph 后续作为共享契约下的对照适配器。
- Markdown 是默认可移植输出；Obsidian 是可选阅读端，不是代码存放位置。
