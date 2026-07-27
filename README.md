<p align="center">
  <strong>简体中文</strong> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <img src="assets/readme-hero.svg" width="100%" alt="AI Intelligence Radar — Signals, Evidence, Knowledge, Trends" />
</p>

<h1 align="center">🛰️ AI Intelligence Radar</h1>

<p align="center">
  <strong>把一手 AI 动态变成可追溯的判断，再沉淀为自己的长期知识库。</strong>
</p>

<p align="center">
  <a href="https://github.com/jj1292/ai-intelligence-radar/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/jj1292/ai-intelligence-radar/test.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=tests&color=22C55E" alt="Tests" /></a>
  <img src="https://img.shields.io/badge/version-v0.5.0-7C3AED?style=for-the-badge" alt="Version v0.5.0" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-2563EB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/license-MIT-06B6D4?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenAI-Codex-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI Codex" />
  <img src="https://img.shields.io/badge/Anthropic-Claude-D97706?style=flat-square&logo=anthropic&logoColor=white" alt="Anthropic Claude" />
  <img src="https://img.shields.io/badge/Google-Gemini-4285F4?style=flat-square&logo=googlegemini&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/X-Signals-111827?style=flat-square&logo=x&logoColor=white" alt="X Signals" />
  <img src="https://img.shields.io/badge/Reddit-Community-FF4500?style=flat-square&logo=reddit&logoColor=white" alt="Reddit Community" />
  <img src="https://img.shields.io/badge/Markdown-Knowledge-0F766E?style=flat-square&logo=markdown&logoColor=white" alt="Markdown Knowledge Base" />
</p>

<p align="center">
  <a href="#-为什么做这个项目">为什么</a> ·
  <a href="#-系统如何工作">工作流</a> ·
  <a href="#-30-秒体验">快速开始</a> ·
  <a href="#-输出目录">输出</a> ·
  <a href="#%EF%B8%8F-roadmap">Roadmap</a>
</p>

---

## ✨ 为什么做这个项目

每天的信息很多，但真正能改变认知的信号很少。这个项目不追求“抓得最多”，而是建立一条从信息到判断的可靠链路。

| 🛰️ 一手信号 | 🧠 认知卡片 | 📈 趋势雷达 |
| --- | --- | --- |
| 跟踪官方发布、官方仓库、X 一手账号和 Reddit 社区 | 每条内容回答“发生了什么、为什么重要、证据是什么” | 只有多个独立信号连续出现，才升级为趋势候选 |

> [!TIP]
> **目标不是替你读完互联网，而是每天留下少量、可复核、以后还能用的知识。**

> [!NOTE]
> **v0.5 已接入实验性的本地 X 订阅：登录凭证留在本机，Agent 成功生成卡片和日报后才推进增量检查点。第一版仍使用确定性 Planner，下一阶段再接模型 Planner。**

## 🌈 当前能力

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🔭 Source Radar</h3>
      <p>统一管理 Codex、Claude、Gemini、X、Reddit 等来源，并记录采集方式与授权状态。</p>
    </td>
    <td width="50%" valign="top">
      <h3>🧭 Source Tiers</h3>
      <p>T1 官方事实、T2 一手账号、T3 社区信号分级，防止把热度误写成结论。</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🗂️ Knowledge Cards</h3>
      <p>输出可移植 Markdown，保留时间、公司、主题、短证据和影响判断，可选用 Obsidian 阅读。</p>
    </td>
    <td width="50%" valign="top">
      <h3>📡 Trend Detection</h3>
      <p>至少两条独立信号才进入趋势候选，并持续观察跨公司、跨来源的变化。</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>⚙️ Observable Loop</h3>
      <p>RunState 驱动采集、过滤、报告、日报和停止；每次规划与工具调用均写入 JSONL Trace。</p>
    </td>
    <td width="50%" valign="top">
      <h3>⏱️ 48h Freshness Gate</h3>
      <p>默认排除 48 小时以外及未来时间信号，并将同一来源连续发布与独立趋势证据区分开。</p>
    </td>
  </tr>
</table>

## 🧩 来源矩阵

| 等级 | 来源 | 角色 | 当前状态 |
| :---: | --- | --- | :---: |
| 🟣 **T1** | 官方 Release Notes、Newsroom、官方 GitHub | 事实底座 | ![ready](https://img.shields.io/badge/READY-22C55E?style=flat-square) |
| 🔵 **T2** | 官方与核心团队 X 账号 | 一手补充、扩散信号 | ![experimental](https://img.shields.io/badge/LOCAL_AUTH-F59E0B?style=flat-square) |
| 🟠 **T3** | Reddit AI 社区 | 问题、用例、情绪和弱信号 | ![auth](https://img.shields.io/badge/AUTH_REQUIRED-F59E0B?style=flat-square) |

已注册 **10 个来源入口**：2 个 GitHub Atom 源可直接采集，X 来源可在本机授权后显式运行，6 个官方网页源与 Reddit 仍等待适配。详见 [`config/sources.json`](config/sources.json)。

## 🔄 系统如何工作

```mermaid
flowchart LR
    A["💻 GitHub Releases"] --> E["⚙️ Agent Loop"]
    B["🏢 官方发布"] --> E
    C["𝕏 / Reddit"] --> E
    E --> F["⏱️ 48h + 去重"]
    F --> G["🧭 证据与来源门"]
    G --> H["🗂️ 情报卡片"]
    G --> I["📡 趋势雷达"]
    G --> J["📰 AI Pulse 日报"]
    E --> T["🧾 JSONL Trace"]

    classDef source fill:#EEF2FF,stroke:#6366F1,color:#312E81,stroke-width:2px;
    classDef process fill:#ECFEFF,stroke:#06B6D4,color:#164E63,stroke-width:2px;
    classDef insight fill:#F5F3FF,stroke:#8B5CF6,color:#4C1D95,stroke-width:2px;
    classDef output fill:#FAE8FF,stroke:#C026D3,color:#701A75,stroke-width:2px;
    class A,B,C source;
    class E,F process;
    class G insight;
    class H,I,J,T output;
```

**AI Pulse 是 Radar Agent 生成的日报格式，不是第二个项目。** Dify 可用于可视化编排和框架对照，详见 [`Dify 可选适配器`](docs/adapters/dify.md)。

## ⚡ 30 秒体验

### 1. 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

### 2. 运行真实 Radar Agent

```bash
python3 -m agent.runner --output outputs/latest-radar --hours 48
```

运行时会读取 OpenAI Codex 与 Anthropic Claude Code 官方 Release，输出知识卡片、趋势雷达、AI Pulse 日报和完整工具 Trace。

### 3. 可选：订阅 X 官方账号

建议使用专用 X 账号。在浏览器登录后，从 X 的 Cookie 中取得 `auth_token` 和 `ct0`，然后运行：

```bash
python3 -m tools.x_twscrape setup <你的X用户名>
python3 -m tools.x_twscrape status
python3 -m agent.runner --source x_frontier_ai_accounts --output outputs/x-radar --hours 48
```

Cookie 通过终端隐藏输入，不会显示在屏幕上；不要把它发到聊天、Issue 或提交到 Git。首次运行会采集配置中的 OpenAI、Anthropic、Google DeepMind 和 Google AI 官方账号，后续只处理新增内容。完整说明见 [`X 本地订阅适配器`](docs/adapters/x-twscrape.md)。

### 4. 运行测试与严格评测

```bash
python3 -m unittest discover -s tests -v
python3 evaluate_radar.py --strict
```

![tests](https://img.shields.io/badge/tests-35%20passed-22C55E?style=for-the-badge&logo=checkmarx&logoColor=white)

当前基线：**3 个案例全部通过，平均分 2.0/2**。真实运行样例读取 20 条官方 Release，保留 2 条 48 小时内信号，并诚实判定“尚无两个独立来源构成趋势”。查看 [`趋势报告`](examples/output/v0.4-live-final/trends/2026-07-27-trend-radar.md)、[`AI Pulse 日报`](examples/output/v0.4-live-final/briefings/2026-07-27-ai-pulse.md) 与 [`Agent Trace`](examples/output/v0.4-live-final/agent-trace-v0.4-unified.jsonl)。

## 🧪 评估先行

AI 产品不能只看一次输出是否“像样”。本项目从六个维度持续评估同一组真实任务：

| 维度 | 核心问题 |
| --- | --- |
| 🎯 相关性 | 应该出现的趋势是否出现，噪声是否被挡住？ |
| 🔗 证据完整性 | 是否保留时间、短证据和原始来源？ |
| 🧭 覆盖度 | 任务要求的关键信号是否完整？ |
| ⏱️ 去重与时效 | 重复和过期信息是否被排除？ |
| 💡 判断价值 | 是否解释“为什么重要”并标注判断边界？ |
| ⚙️ 过程可靠性 | 卡片、趋势报告与运行状态是否一致？ |

每项使用 `0 / 1 / 2` 三档评分，并设置来源混淆、链接缺失、编造证据、凭证泄露和越权操作等一票否决项。完整规则见 [`evals/rubric.md`](evals/rubric.md)。

## 💜 输出目录

```text
ai-intelligence-radar/
├── signals/
│   └── 2026-07-22/
│       ├── openai-xxxxxxxxxx.md
│       ├── anthropic-xxxxxxxxxx.md
│       └── community-xxxxxxxxxx.md
├── trends/
│   └── 2026-07-22-trend-radar.md
├── briefings/
│   └── 2026-07-22-ai-pulse.md
└── agent-trace-xxxxxxxx.jsonl
```

Markdown 是默认可移植格式，可以放在任意目录；Obsidian 只是可选阅读端，不是项目代码存放位置。

每张卡片固定包含：

- 🔗 原始来源与发布时间
- 🏢 公司、平台和来源等级
- 📝 一句话结论
- 💡 为什么重要
- 🔎 可回到原文核验的短证据
- 🎯 影响评分、可信度与判断边界

规范定义见 [`schemas/intelligence-signal.schema.json`](schemas/intelligence-signal.schema.json)。

## 🔐 平台与数据边界

> [!IMPORTANT]
> - 当前 X 适配器基于非官方 `twscrape`，免费但可能因 X 接口变化失效，也有账号风控风险；建议使用专用账号。
> - 生产环境优先使用 X 官方 API；本地实验凭证只保存在 `~/.ai-intelligence-radar/twscrape.db`。
> - Reddit 使用 OAuth，并遵守平台的数据使用与留存要求。
> - API Key、Token 和 OAuth 凭证只能进入本地环境变量或 GitHub Secret。
> - 知识库保存链接、必要元数据、短证据和衍生判断，不批量复制完整平台内容。
> - T3 社区热度必须经过 T1 官方来源或复现实验交叉验证。

## 🗺️ Roadmap

| 版本 | 主题 | 状态 |
| :---: | --- | :---: |
| `v0.1` | AI Pulse 简报原型、输入契约、测试与 CI | ✅ Done |
| `v0.2` | 来源注册表、情报 Schema、Markdown 卡片、趋势雷达 | ✅ Done |
| `v0.3` | Eval Contract、3 个基线案例、评分器与可复现报告 | ✅ Done |
| `v0.4` | GitHub Atom、48 小时时效、RunState、最小 Loop、AI Pulse 输出、Trace | ✅ Done |
| `v0.5` | 本地 X 订阅、来源分发、成功后增量 Checkpoint、账号安全边界 | 🚧 Current |
| `v0.6` | 模型 Planner、通用 Resume、官方网页、Reddit OAuth | 🧭 Next |
| `v1.0` | 记忆、回放评测、周/月复盘、主题订阅与来源质量评分 | 🌟 Vision |

## 📚 文档

- 🗺️ [`项目总览`](PROJECT.md)
- 📘 [`v0.2 PRD`](docs/PRD-AI-Intelligence-Radar-v0.2.md)
- 🧠 [`Agent Harness 架构构思`](docs/agent-harness-architecture.md)
- 🎯 [`AI 产品评估与 Agent 评测指南`](docs/ai-product-evaluation-guide.md)
- 🔌 [`Dify 可选适配器`](docs/adapters/dify.md)
- 𝕏 [`X 本地订阅适配器`](docs/adapters/x-twscrape.md)
- 🧭 [`从 AI Pulse 到 Radar`](docs/history/from-ai-pulse-to-radar.md)
- 🧩 [`情报信号 Schema`](schemas/intelligence-signal.schema.json)
- 📡 [`来源注册表`](config/sources.json)
- 🧪 [`评测规则`](evals/rubric.md)
- 📊 [`v0.3 基线报告`](evals/baseline-report.md)
- 🧾 [`v0.4 真实运行 Trace`](examples/output/v0.4-live-final/agent-trace-v0.4-unified.jsonl)
- 📝 [`Changelog`](CHANGELOG.md)

---

<p align="center">
  <strong>如果这个项目也能帮你减少信息焦虑、建立自己的 AI 判断，欢迎点一个 ⭐ Star。</strong>
</p>

<p align="center">
  Built with <strong>Python</strong> · <strong>Agent Loop</strong> · <strong>JSONL</strong> · <strong>Markdown</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-06B6D4?style=flat-square" alt="MIT License" /></a>
</p>
