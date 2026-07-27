# PRD：AI Intelligence Radar v0.2

> 历史版本说明：本文记录 v0.2 的产品假设。自 v0.4 起，项目以自研 Agent Harness 为核心，Markdown 为默认可移植输出；Dify 与 Obsidian 分别是可选适配器和阅读端。当前口径见 `PROJECT.md` 与 `docs/project-status.md`。

## 1. Summary

AI Intelligence Radar 将原来的“每日 AI 新闻摘要”升级为个人 AI 行业情报与知识系统。它持续收集官方发布、官方代码仓库、X 一手账号和 Reddit 社区信号，经过分级、去重、判断和趋势聚合后，写入可长期复用的 Obsidian 知识库。

## 2. Contacts

| 角色 | 联系人 | 说明 |
| --- | --- | --- |
| 产品负责人 | JOJO | 决定关注主题、来源范围和最终认知输出 |
| 实现与验证 | Codex | 代码、测试、文档和 GitHub 交付 |

## 3. Background

当前项目能把输入整理成简报，但仍停留在“单日内容”。它缺少稳定来源清单、来源等级、知识卡片和跨日趋势，因此很难形成持续认知。

现在适合升级，因为主要厂商已经提供可监控的官方更新入口：Codex 有产品更新和官方仓库，Claude 有平台 Release Notes、Newsroom 和 Claude Code 仓库，Gemini 有 API Release Notes。X 的 Recent Search 可检索近 7 天内容，但需要开发者项目和 Token；Reddit 要求按 OAuth 与 Data API 条款访问，并限制数据用途和留存。[X Search Posts](https://docs.x.com/x-api/posts/search/introduction) · [Reddit Data API Terms](https://redditinc.com/policies/data-api-terms) · [Claude Release Notes](https://platform.claude.com/docs/en/release-notes/overview) · [Gemini API Release Notes](https://ai.google.dev/gemini-api/docs/changelog)

## 4. Objective

目标不是抓得最多，而是每天获得少量、可追溯、能改变判断的信号，并逐渐形成自己的 AI 行业知识图谱。

首期 Key Results：

- 100% 已发布卡片包含原始链接、发布时间、公司、主题和“为什么重要”。
- T1 官方来源覆盖 OpenAI/Codex、Anthropic/Claude、Google/Gemini 三条主线。
- 重复事件率低于 5%，社区信号不会在缺少官方证据时被写成确定事实。
- 每日可生成知识卡片和趋势雷达；至少两条独立信号才进入“趋势候选”。
- API Key、Token 和 OAuth 凭证不进入仓库或 Obsidian。

## 5. Market Segment(s)

首要用户是需要持续理解 AI 产品、模型和智能体变化的个人从业者。核心任务不是“看新闻”，而是：

- 快速知道今天哪些变化值得看；
- 判断变化对产品、技术和职业决策的影响；
- 回顾一个主题如何连续演化；
- 在需要写方案、做竞品或做决策时快速复用证据。

## 6. Value Proposition(s)

- 从信息流变成认知流：每条内容必须回答“发生了什么、为什么重要、证据是什么”。
- 官方与社区分层：官方发布是事实底座，X 是一手扩散信号，Reddit 是用户问题和情绪信号。
- 从单条到趋势：只有跨来源、跨公司或跨日期重复出现的主题才升级为趋势。
- 默认进入 Obsidian：卡片可搜索、可链接、可补充个人判断，而不是困在一次性简报里。

## 7. Solution

### 7.1 用户流程

```text
来源注册表 → 定时采集 → 规范化 → 去重 → 来源分级
           → 重要性判断 → 情报卡片 → 趋势聚合 → Obsidian
```

用户每天只需要看“趋势雷达”和少量高分卡片；需要深入时再回到原始链接。

### 7.2 Key Features

1. 来源注册表：记录公司、入口、来源等级、采集方式和授权要求。
2. 情报信号 Schema：统一标题、来源、公司、时间、主题、摘要、影响与证据。
3. 知识卡片：生成 Obsidian Markdown，不保存整篇平台内容。
4. 趋势雷达：统计跨信号主题，只把两条以上独立信号列为趋势候选。
5. 平台合规：X 和 Reddit 适配器默认关闭，拿到合规凭证后再启用。

### 7.3 Technology

- Dify：负责定时触发、网页/工具采集、LLM 评分和结构化输出。
- Python：负责 Schema 校验、去重、知识卡片和趋势文件生成。
- Obsidian：个人知识库和长期复盘界面。
- GitHub Actions：负责代码测试，不存放平台密钥。

### 7.4 Assumptions

- 用户愿意逐步配置 X Developer 与 Reddit OAuth；若不配置，系统仍可依赖官方更新入口工作。
- 官方页面结构可能变化，因此网页采集需要监控失败率并保留人工补录入口。
- 社区热度与真实产品价值不等价，需要用 T1 来源或复现实验校正。
- 原 Dify DSL 尚未提供，当前先定义输入输出契约，后续再导入和对账。

## 8. Release

### v0.2（当前版本）

- 来源注册表与来源等级；
- 情报信号 Schema；
- Obsidian 知识卡片与趋势雷达生成器；
- 示例数据、测试和 PRD。

### v0.3（下一阶段）

- 官方 Atom/Release Notes 采集器；
- X Recent Search 与 Reddit OAuth 适配器；
- 48 小时时效、事件级去重和失败重试。

### v0.4

- 导入原 Dify DSL；
- LLM 重要性评分、证据检查和每日调度；
- 自动写入个人 Obsidian 项目目录。

### v1.0

- 周/月趋势复盘；
- 主题订阅、来源质量评分和评测集；
- 监控采集覆盖率、重复率、误报率和知识复用率。
