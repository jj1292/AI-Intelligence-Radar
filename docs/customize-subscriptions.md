# 修改订阅源 / Customize Sources

日常只需要编辑 [`config/subscriptions.json`](../config/subscriptions.json)。这个文件保存公开来源，不保存账号密码、Cookie、Token 或 API Key。

## 在 GitHub 网页修改

1. 打开 `config/subscriptions.json`；
2. 点击右上角铅笔；
3. 增加、删除或暂停来源；
4. 点击 `Commit changes`。

提交后，`publish-subscription-feeds` 会自动运行。完成后，原来的 RSS 和 JSON 地址会继续使用，不需要通知订阅者更换链接。

## GitHub Release

在 `github_releases` 中增加一个对象：

```json
{
  "repo": "owner/repository",
  "company": "Company name",
  "topics": ["agents", "developer-tools"],
  "enabled": true
}
```

`repo` 必须是 GitHub URL 中的 `owner/repository`。项目会自动转换为 `https://github.com/owner/repository/releases.atom`。

## Claude / Anthropic 官方博客

`official_web` 已默认启用 Anthropic Newsroom：

```json
{
  "id": "anthropic_newsroom",
  "adapter": "anthropic_news",
  "name": "Anthropic Newsroom",
  "url": "https://www.anthropic.com/news",
  "company": "Anthropic",
  "topics": ["claude", "products", "research", "safety", "company"],
  "enabled": true
}
```

Anthropic 官网当前没有可用的官方 RSS/Atom，因此项目直接读取官方 Newsroom 页面。该适配器只支持 Anthropic 官方页面；其他没有 Feed 的网页需要单独增加适配器。

## 任意 RSS 或 Atom

在 `rss_feeds` 中增加一个对象：

```json
{
  "name": "Official product updates",
  "url": "https://example.com/feed.xml",
  "company": "Example AI",
  "source_tier": 1,
  "channel": "official",
  "topics": ["models", "products"],
  "enabled": true
}
```

只有来源本身提供 RSS 或 Atom 时才能使用。`source_tier` 可填 `1`、`2` 或 `3`。

## Reddit 社区

直接修改 `reddit.communities`：

```json
"communities": ["LocalLLaMA", "MachineLearning", "OpenAI"]
```

多个社区会合并成一次 Reddit 公共 RSS 请求，减少限速。`max_results` 控制一次最多读取多少条，范围是 `1` 到 `100`。

Reddit 是 T3 社区信号，只适合发现问题、用例和情绪；重要结论仍需回到 T1 官方来源核验。

## X 账号

在 `x.accounts` 中增加一个对象：

```json
{
  "username": "OpenAI",
  "company": "OpenAI",
  "enabled": true
}
```

不要写 `https://x.com/`，只写用户名，带不带 `@` 都可以。X 来源只有在仓库维护者配置后台发布账号后才运行；普通订阅者始终不需要 X 账号。

## 暂停来源

将来源或整组的：

```json
"enabled": true
```

改为：

```json
"enabled": false
```

这样可以保留配置，之后随时恢复。

## 修改后的检查

GitHub 测试会自动检查 JSON 格式、重复 ID、GitHub 仓库格式、Reddit 社区名和 X 用户名。也可以在本地运行：

```bash
python3 source_registry.py --config config/subscriptions.json
python3 -m unittest discover -s tests -v
```

如果发布时某个外部来源暂时不可用，Agent 会记录该来源错误并继续处理其他成功来源；只有所有来源都失败时，整次运行才会失败。

---

## English Quick Guide

Edit only [`config/subscriptions.json`](../config/subscriptions.json) for day-to-day source changes. Add GitHub repositories under `github_releases`, generic feeds under `rss_feeds`, subreddit names under `reddit.communities`, and X usernames under `x.accounts`.

Commit the file on GitHub to trigger `publish-subscription-feeds` automatically. Existing public RSS/JSON URLs remain unchanged. Set `"enabled": false` to pause a source. Never place cookies, tokens, passwords, or API keys in this file; maintainer-only credentials belong in GitHub Secrets.
