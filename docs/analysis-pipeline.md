# 正文分析流水线

重要信号不是“官方来源摘要”的别名。v0.9 只有在 Agent 读完正文并完成结构化分析后，才允许内容进入重要信号区。

## 运行顺序

```text
采集 → 时效与去重 → 读取正文 → 模型分析 → Insight Contract → 知识卡 / Feed / 网站
```

`analyze_signals` 位于过滤与输出之间。官方文章优先读取原文正文；正文读取失败时不生成分析。GitHub Release、X 等短内容使用来源自带的完整文本。Reddit 只进入实时情报，不自动升级为重要信号。

## Insight Contract

每条分析必须同时包含：

- `core_idea`：作者真正建立的核心主张或变化；
- `key_points`：2–5 个事实、机制、数字、约束或承诺；
- `analysis`：相对现状的变化、实现机制、代价限制及决策影响；
- `takeaway`：可以更新认知或指导行动的结论。

系统明确禁止使用“这是官方一手信息”“值得关注”“可用于跟踪”等来源套话代替分析。没有完整 Insight Contract 的内容只出现在实时情报。

## 模型与成本控制

GitHub Actions 使用仓库自动提供的 `GITHUB_TOKEN` 调用 GitHub Models，工作流只申请 `models: read` 权限，不需要新增模型 API Key。默认模型为 `openai/gpt-4.1`，可通过 `RADAR_ANALYSIS_MODEL` 更换。

- 每轮最多分析 6 条新信号；
- 已有分析从 `docs/feed.json` 复用；
- 模型或正文读取失败不会生成伪分析；
- 原文被视为不可信数据，其中的指令不会被执行。

GitHub Models 的权限和调用方式以 [GitHub 官方文档](https://docs.github.com/en/rest/models/inference) 为准。
