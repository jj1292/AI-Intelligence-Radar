# AI Intelligence Radar 项目状态

更新日期：2026-07-28

## 当前定位

AI Intelligence Radar 是一个可观察、可评测的 AI 行业情报 Agent 与 Agent Harness 学习工程。它把官方发布和社区信号转化为可追溯的知识卡片、趋势判断和 AI Pulse 日报。

AI Pulse 已从独立项目名调整为日报输出格式；Dify 已调整为可选适配器，不再代表核心架构。

## v0.7.1 当前进展

- 分支：`main`，v0.7 功能提交 `3cb5195`、首个动态 Feed 提交 `8c93dd4` 已发布；
- 日常入口：`config/subscriptions.json`，支持 GitHub Release、RSS/Atom、Reddit 社区与 X 账号；
- 默认真实来源：Anthropic 官方 Newsroom，OpenAI Codex、Anthropic Claude Code、Google Gemini CLI Release，以及 LocalLLaMA、MachineLearning、OpenAI Reddit 社区；
- Agent 核心：RunState、确定性 Planner、Tool Registry、停止条件；
- 来源分发：GitHub Atom、通用 RSS/Atom 与 Reddit 公共 RSS 可直接运行；X 由维护者授权的后台发布器统一运行；
- 工具步骤：`collect_source`、`filter_signals`、`write_report`、`write_briefing`、`write_feed`、`commit_checkpoints`；
- 可靠性：48 小时时效门、未来时间保护、独立来源趋势门；
- 可观察性：每次 Planner 决策与工具调用写入 JSONL Trace；
- 输出：Markdown 知识卡片、趋势雷达、AI Pulse 日报；
- 订阅输出：滚动 RSS 2.0 与 JSON Feed 1.1，最多保留 200 条；
- 公开地址：RSS 与 JSON Feed 已由 GitHub Pages 匿名提供，当前 38 条，包含 Reddit 25 条、Gemini CLI 3 条、OpenAI 8 条、Anthropic 2 条；
- 可修改性：清单提交会立即触发发布，定时任务也动态读取同一文件，不再写死来源；
- 评测：59 项测试、3/3 严格评测通过；Anthropic Newsroom 真实页面识别 13 篇、168 小时窗口筛选 5 篇、0 个工具错误。
- X 可靠性：`since_id` 增量读取，Feed 成功发布后才提交检查点；账号数据库与 Cookie 不进入 Git。

## 当前限制

- Planner 仍是确定性基线，还没有接入模型决策；
- 已实现 X 来源检查点，但尚未形成跨所有工具的通用 Resume、幂等和自动重试；
- 没有 RSS/Atom 的官方网页仍等待专用采集适配器；
- X 免费路线依赖非官方接口，存在失效、限速和账号风控风险；生产仍需官方 API；
- GitHub Pages 已启用；X 发布器账号变量与 Cookie Secret 尚未配置，因此当前公开 Feed 先覆盖 GitHub Release；
- Reddit 公共 RSS 已可用，但仍可能受平台限速影响；多个社区已合并成一次请求；
- 评测集只有 3 个案例，尚不足以覆盖长期运行风险。

## 下一步

1. 根据实际阅读体验调整订阅清单，重点观察 Reddit 25 条是否占比过高。
2. 确认专用 X 后台发布账号；配置变量与 Cookie Secret 后完成首次 X Feed 发布。
3. 增加模型 Planner，并与确定性 Planner 使用同一 Tool Contract 对照评测。
4. 把 X 的来源检查点扩展为通用 Resume，并增加重试与幂等。
5. 扩展无 RSS 官方网页采集器，并将评测集扩展到 12 个案例。

## 项目边界

- 源码、架构、评测和运行产物只放在独立项目目录；
- Markdown 可输出到任意目录，Obsidian 只是可选阅读端；
- 不提交密钥、Token、OAuth 凭证或未脱敏的 Dify DSL；
- 不通过刷 Star、虚假提交或机器人互赞制造活跃度。

项目地址：https://github.com/jj1292/AI-Intelligence-Radar
