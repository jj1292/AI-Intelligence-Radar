# Firecrawl 可选网页适配器

Firecrawl 适合抓取没有 RSS/Atom、又经常使用 JavaScript 渲染的官方博客或新闻列表。AI Intelligence Radar 把它放在来源路由的最后一层：

```text
RSS / Atom → 专用官方适配器 → Firecrawl 通用适配器 → 只跳过失败来源
```

它不会替代 Anthropic Newsroom 的专用采集器，也不会用于 X 或 Reddit。

## 配置来源

在 `config/subscriptions.json` 的 `official_web` 中加入：

```json
{
  "id": "example_newsroom",
  "adapter": "firecrawl",
  "name": "Example Newsroom",
  "url": "https://example.com/news",
  "company": "Example AI",
  "topics": ["agents", "products", "research"],
  "max_results": 30,
  "enabled": true
}
```

然后在 GitHub 仓库 `Settings → Secrets and variables → Actions` 增加 Repository Secret：

```text
FIRECRAWL_API_KEY
```

Key 不进入网页、配置文件、日志或 Git 提交。

## 运行方式

适配器调用 Firecrawl v2 `POST /scrape`，使用 JSON Schema 提取：

- 文章标题；
- 原文 URL；
- 发布时间；
- 短摘要；
- 分类。

结果再进入与 GitHub、RSS、X、Reddit 相同的 Intelligence Signal 契约、时效门、去重、Feed 与 Checkpoint 流程。单个 Firecrawl 来源失败时，Agent 会记录错误并继续其他成功来源。

## 边界

- 优先使用来源自己的 RSS/Atom，成本更低、结构也更稳定。
- 有稳定页面结构的核心来源优先写专用适配器，结果更可控。
- Firecrawl JSON 抽取依赖页面内容和模型，可信度默认低于专用官方适配器。
- Firecrawl Cloud 的额度与价格可能变化，启用前应查看其当前方案。
- 自托管适合数据控制和学习，但官方说明自托管版不包含 Fire-engine 的部分高级反屏蔽能力。

官方资料：

- [Firecrawl v2 Scrape API](https://docs.firecrawl.dev/api-reference/endpoint/scrape)
- [Firecrawl Scrape formats and JSON extraction](https://docs.firecrawl.dev/features/scrape)
- [Firecrawl self-hosting limitations](https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md)
