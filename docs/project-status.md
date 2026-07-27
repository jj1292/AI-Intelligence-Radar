# AI Intelligence Radar 项目状态

更新日期：2026-07-27

## 当前定位

AI Intelligence Radar 是一个可观察、可评测的 AI 行业情报 Agent 与 Agent Harness 学习工程。它把官方发布和社区信号转化为可追溯的知识卡片、趋势判断和 AI Pulse 日报。

AI Pulse 已从独立项目名调整为日报输出格式；Dify 已调整为可选适配器，不再代表核心架构。

## v0.4 当前进展

- 分支：`main`，v0.4 已合并并完成 GitHub Actions 验证；
- 真实来源：OpenAI Codex、Anthropic Claude Code GitHub Release Atom；
- Agent 核心：RunState、确定性 Planner、Tool Registry、停止条件；
- 工具步骤：`collect_source`、`filter_signals`、`write_report`、`write_briefing`；
- 可靠性：48 小时时效门、未来时间保护、独立来源趋势门；
- 可观察性：每次 Planner 决策与工具调用写入 JSONL Trace；
- 输出：Markdown 知识卡片、趋势雷达、AI Pulse 日报；
- 评测：3/3 案例通过，平均 2.0/2。

## 当前限制

- Planner 仍是确定性基线，还没有接入模型决策；
- 尚未实现 Checkpoint/Resume、幂等和自动重试；
- 6 个官方网页来源等待采集适配器；
- X 和 Reddit 等待合规 OAuth/API 授权；
- 评测集只有 3 个案例，尚不足以覆盖长期运行风险。

## 下一步

1. 增加模型 Planner，并与确定性 Planner 使用同一 Tool Contract 对照评测。
2. 增加 Checkpoint/Resume、预算、重试与幂等。
3. 扩展官方网页采集器，再接入 X 和 Reddit。
4. 将评测集扩展到 12 个案例并加入固定 Feed 回放。

## 项目边界

- 源码、架构、评测和运行产物只放在独立项目目录；
- Markdown 可输出到任意目录，Obsidian 只是可选阅读端；
- 不提交密钥、Token、OAuth 凭证或未脱敏的 Dify DSL；
- 不通过刷 Star、虚假提交或机器人互赞制造活跃度。

项目地址：https://github.com/jj1292/AI-Intelligence-Radar
