---
type: project-home
status: active
project: AI Intelligence Radar
version: 0.7.0
updated: 2026-07-28
---

# AI Intelligence Radar：行业情报 Agent 与 Harness 学习工程

## 目标

持续收集 Codex、Claude、Gemini 等顶尖 AI 公司和产品的一手信息，并结合 X 官方账号与 Reddit 社区信号，形成可追溯的行业判断和长期知识资产。

重点不是“每天看更多新闻”，而是：

- 知道真正发生了什么；
- 判断为什么重要；
- 区分官方事实、团队观点和社区情绪；
- 观察一个主题如何跨公司、跨时间连续演化；
- 在产品规划、竞品分析和职业决策中快速复用证据。

## 信息流

```text
官方发布 / GitHub / X / Reddit
              ↓
Agent Loop：采集 → 时效/去重 → 证据门 → 输出 → 停止
              ↓
 情报卡片 + 趋势雷达 + AI Pulse 日报 + RSS/JSON + JSONL Trace
```

## 来源等级

- T1：公司官方 Release Notes、Newsroom、官方代码仓库，是事实底座。
- T2：官方或核心团队 X 一手账号，用于补充发布背景和传播信号。
- T3：Reddit 等社区，用于发现真实问题、用例和情绪，不单独作为事实依据。

## 独立项目目录

项目源码、设计、评测与运行产物统一放在独立目录 `/Users/wingsjing/Documents/Codex/ai-intelligence-radar`，不再放入 Obsidian Vault：

```text
ai-intelligence-radar/
├── PROJECT.md                       # 项目总览
├── agent/                           # Planner、RunState 与 Loop
├── tools/                           # 采集与领域工具
├── reporters/                       # AI Pulse 等输出适配器
├── runtime/                         # Trace 与后续 Checkpoint
├── docs/                            # 架构、PRD、适配器与演进历史
├── evals/                           # 案例、规则与基线报告
├── config/                          # 来源配置
├── schemas/                         # 情报信号契约
├── examples/                        # 脱敏演示数据
└── tests/                           # 自动化测试
```

所有 Markdown 输出通过 `--output` 显式指定位置，不默认写入 Obsidian。Obsidian 是可选阅读端，不是项目代码目录。每张情报卡片必须保留原始链接、发布时间、公司、来源等级、主题、摘要、为什么重要和证据边界；默认不复制整篇平台内容。

## 当前版本

### v0.2.0

- 已建立 10 个来源入口注册表；
- 已定义 Intelligence Signal Schema；
- 已实现可移植 Markdown 情报卡片和趋势雷达生成器；
- 至少两条独立信号才进入趋势候选；
- X 和 Reddit 处于待合规授权状态，不绕过平台限制抓取；
- 示例数据只用于代码验证，不写入本知识库。
- GitHub 项目 README 已完成彩色视觉与中英文双语升级。

### v0.3.0（评测基线）

- 已建立 3 个可复现案例：正常、边界和风险场景；
- 已实现相关性、证据、覆盖度、去重与时效、判断价值、过程可靠性六维评分；
- 当前基线为 2/3 案例通过，平均 1.89/2；
- 已明确暴露“48 小时外旧信号仍被输出”的产品缺口；
- PR #4 与 PR #5 已依次 squash 合并；v0.3 已进入 `main`，合并提交为 `6f82dc6`，最终 Actions run #12 成功。

### v0.4.0（最小 Agent Harness）

- 已实现 OpenAI Codex 与 Anthropic Claude Code GitHub Atom 真实采集；
- 已实现 48 小时时效过滤和未来时间保护；
- 已建立 RunState、Tool Registry、确定性 Planner、停止条件和 JSONL Trace；
- 已将 AI Pulse 从旧项目名迁移为 Agent Loop 的 `write_briefing` 日报输出工具；
- 所有来源失败时 Run 明确失败，单个来源失败时保留错误并继续；
- 趋势门槛改为至少两个独立的公司/来源组合，避免同仓库连续发版制造虚假趋势；
- 评测基线已提升为 3/3 通过，平均 2.0/2；
- 真实样例读取 20 条官方 Release，保留 2 条 48 小时内信号，0 个工具错误。

### v0.5.0（X 后台采集）

- 已实现按 `collection_mode` 分发 GitHub Atom 与 X 采集器；
- 已接入 `twscrape` 本地 Cookie 授权，凭证默认保存在用户主目录，不进入项目仓库；
- 已将官方与核心团队 X 内容标准化为 T2 信号，并保留公司映射和原帖链接；
- 已实现 `since_id` 增量检查点，且只在卡片、趋势和日报成功生成后提交；
- 已支持账号状态检查和 Cookie 过期后的显式重新授权；
- 免费路线用于个人低频实验，生产稳定性仍以 X 官方 API 为准。

### v0.6.0（公开订阅发布器）

- 将 X 账号认证从订阅者入口移到后台采集层；
- 已实现滚动 RSS 2.0 和 JSON Feed 1.1，最多保留 200 条并按链接去重；
- Feed 发布已纳入 Agent Loop，成功后才提交来源检查点；
- 已增加 GitHub Actions 定时发布器，维护者配置一次，普通用户直接订阅公开 URL；
- 后台缺少 Secret 时只跳过 X 并继续发布公开来源，不打印或提交 Cookie；
- 公开 Feed 数据由 GitHub Pages `/docs` 目录提供。

### v0.7.0（可编辑订阅源）

- 新增面向维护者的 `config/subscriptions.json`，日常无需修改 Python；
- 支持直接增删 GitHub Release、任意 RSS/Atom、Reddit 社区和 X 账号；
- 多个 Reddit 社区合并为一次公开 RSS 请求，无需 OAuth，并降低连续请求限速；
- 自动发布器不再写死来源：订阅清单提交后立即触发更新，定时任务也读取同一清单；
- X 凭证缺失时只跳过 X，GitHub、RSS 和 Reddit 继续发布；
- Agent 步数预算根据来源数量自动扩展，允许维护者持续增加来源；
- 53 项测试通过；无 X 凭证真实运行读取 55 条、筛选 46 条、0 个工具错误。

## Agent 化升级构思

项目下一阶段拟从确定性情报管道升级为可观察、可恢复、可评测的 Loop Agent，同时作为 Agent Harness 架构实验室。推荐采用“外层确定性状态机 + 内层模型决策循环”，先实现单 Agent 的自研最小 Harness，再分别用 OpenAI Agents SDK、LangGraph 与 Dify 复刻同一任务并进行对照评测。

详细方案：[Agent Harness 架构构思](docs/agent-harness-architecture.md)

评估入门：[AI 产品评估与 Agent 评测指南](docs/ai-product-evaluation-guide.md)。项目采用“评估先行”：先用 3 个最小案例跑通评测闭环，再扩展到 12 个真实案例；通过三档评分和一票否决规则评估现有确定性管道，再判断 Agent 化是否真正提升用户价值。

## 下一步

1. 在 GitHub Actions 首次运行 v0.7 动态发布器，确认线上 Feed 出现 Gemini 与 Reddit 内容。
2. 确认专用 X 后台发布账号并完成首次 X Feed 发布。
3. 将确定性 Planner 替换为可选模型 Planner，并保持同一 Tool Contract。
4. 将 X 的来源检查点扩展为通用 Checkpoint/Resume，并增加重试与幂等。
5. 接入仍未提供 RSS 的官方 Release Notes 网页采集器；生产 X 采集保留官方 API 适配位。
6. 把 3 个最小评测案例扩展到 12 个，并增加真实 Feed 回放集。

## 相关项目

- GitHub：https://github.com/jj1292/AI-Intelligence-Radar
- 本地目录：`/Users/wingsjing/Documents/Codex/ai-intelligence-radar`
