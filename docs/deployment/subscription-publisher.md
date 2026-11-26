# 公开订阅发布器

AI Intelligence Radar 采用“采集端一次认证，订阅端零认证”的发布模式。普通用户只需要 RSS 或 JSON Feed URL；X 账号和 Cookie 仅属于后台发布器。

```text
X / GitHub / RSS / Reddit
          ↓
   定时 Agent 采集
          ↓
时效门 → 去重 → 报告 → RSS/JSON → Checkpoint
                            ↓
                    GitHub Pages 公共地址
                            ↓
                  Feedly / Inoreader / FreshRSS
```

## 普通用户

无需注册、登录或部署，直接订阅：

- RSS：`https://jj1292.github.io/AI-Intelligence-Radar/feed.xml`
- JSON Feed：`https://jj1292.github.io/AI-Intelligence-Radar/feed.json`

## 仓库维护者的一次性配置

### 0. 修改订阅清单

日常只编辑 `config/subscriptions.json`。它支持 GitHub Release、任意 RSS/Atom、Reddit 社区和 X 账号。提交清单后会立即触发发布；详细格式见 [`订阅源修改指南`](../customize-subscriptions.md)。

### 1. 配置后台采集账号（可选）

建议使用专用 X 账号。在 GitHub 仓库进入 `Settings → Secrets and variables → Actions`：

- Repository variable：`X_ACCOUNT_USERNAME`
- Repository secret：`X_COOKIE_AUTH_TOKEN`
- Repository secret：`X_COOKIE_CT0`

Cookie 只保存在 GitHub Actions Secret 中。不要写入 Issue、README、工作流参数、日志或 Git 提交。

如果启用了 `"adapter": "firecrawl"` 的通用网页来源，再增加：

- Repository secret：`FIRECRAWL_API_KEY`

没有配置 Firecrawl Key 时只跳过这类通用网页；Anthropic 专用适配器、GitHub、RSS/Atom 和 Reddit 仍继续运行。

### 2. 启用 GitHub Pages

在 `Settings → Pages → Build and deployment` 中选择：

- Source：`Deploy from a branch`
- Branch：`main`
- Folder：`/docs`

保存后，公开 Feed 地址通常需要几分钟生效。

### 3. 首次发布

打开仓库的 `Actions → publish-subscription-feeds → Run workflow`。此后工作流会在北京时间约 09:17 和 21:17 自动运行。

后台执行顺序为：

1. 从 GitHub Secret 临时建立 `twscrape` 账号数据库；
2. 动态读取 `config/subscriptions.json`，抓取启用的 GitHub Release、RSS/Atom、Reddit 社区、可选 Firecrawl 网页，以及后台已授权时的 X 账号；
3. 通过 72 小时时效门并生成卡片、趋势、AI Pulse 和公开 Feed；
4. 将最多 200 条滚动 Feed 条目与公开 `since_id` 检查点提交到仓库；
5. 只有 Feed 成功写入后才推进检查点。

缺少变量或 Secret 时，工作流只跳过 X，仍会持续发布无需认证的 GitHub、RSS/Atom 和 Reddit 来源；同时不会尝试输出凭证。

## AI 情报晨报

实时情报每小时第 17 分钟采集。台北时间 07:17 的任务同时更新晨报和研究主题，目标 08:00 前发布。GitHub Actions 排队和 Pages 部署决定实际到达时间。

- 编辑 [晨报配置](../../config/morning-edition.json) 维护栏目与检索词。单期最多 10 条，栏目目标配额为 2、2、3、1、2。
- 中美热点使用 Google News RSS 和媒体原始 RSS。公开可索引的公众号与 X 内容参与产品实践检索，已配置账号的 X 收藏候选在滚动 Feed 更新时补入。
- \`intelligence.json\` 同时提供小时热点和重要信号。同事件按标题和发布方去重，可链接到晨报原条目。相同发布方的重复链接只计一次。
- \`research-trends.json\` 汇总近 14 天指定期刊、medRxiv 和 arXiv 的检索样本，期刊和预印本分列。可查看主题和代表论文。样本按标题、DOI 去重，每篇记入一个主要主题。
- 可配置 Actions Secret `RADAR_EDITOR_API_KEY` 启用中文分析，模型可通过 `RADAR_EDITOR_MODEL` 指定。有摘要的条目才会提交给模型。网页展示来源摘要和原文链接，也可从首页订阅晨报 RSS。
- 本地验证命令为 `python -m reporters.morning_edition --output /tmp/radar-morning`。生成器写出当期 JSON、历史索引和 RSS。满 10 条的一期保留其发布快照，人工重建可使用 `--refresh`。当天候选减少时保留较完整的一期。

## 自托管与生产替代

Fork 仓库的开发者只有在运营自己的发布器时才需要配置账号；他们的下游订阅者同样不需要认证。

`twscrape` 依赖 X 内部接口，适合低频个人实验，可能遇到接口变更、限速或账号验证。需要稳定 SLA 时，应将后台 Collector 替换为 X 官方 API；RSS/JSON 输出契约和订阅地址可以保持不变。
