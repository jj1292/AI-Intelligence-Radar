# X 后台采集适配器

`v0.5` 使用 [`twscrape`](https://github.com/vladkens/twscrape) 在采集端读取 X 搜索结果。这是一条免费的实验路线，不是 X 官方 API。它适合个人学习和低频验证，不适合作为需要稳定 SLA 的生产采集服务。

该账号只服务后台发布器。普通订阅者直接读取公开 RSS/JSON，不需要执行本页的任何账号设置。托管发布方式见 [`公开订阅发布器`](../deployment/subscription-publisher.md)。

## 它订阅什么

默认来源 `x_frontier_ai_accounts` 关注以下官方账号：

- `@OpenAI`、`@OpenAIDevs`
- `@AnthropicAI`
- `@GoogleDeepMind`、`@GoogleAI`

查询会排除回复和转发，并优先保留带链接的发布。X 内容被标为 T2 一手信号；涉及产品能力、价格或发布日期的事实，仍应回到 T1 官方文档核验。

## 首次设置

1. 建议使用专门用于订阅的 X 账号，并在浏览器中正常登录。
2. 打开浏览器开发者工具，在 X 站点的 Cookies 中找到 `auth_token` 和 `ct0`。
3. 在项目目录执行：

```bash
python3 -m pip install -r requirements.txt
python3 -m tools.x_twscrape setup <X用户名，不含@>
```

终端随后出现隐藏输入提示。输入格式为：

```text
auth_token=你的值; ct0=你的值
```

不要把真实值写入命令参数、文档、聊天、截图或 Git。完成后检查：

```bash
python3 -m tools.x_twscrape status
```

## 运行订阅

X 来源必须显式选择，普通运行仍只执行无需登录的 GitHub 来源：

```bash
python3 -m agent.runner \
  --source x_frontier_ai_accounts \
  --output outputs/x-radar \
  --hours 48
```

输出包括情报卡片、趋势雷达、AI Pulse 日报和 Agent Trace。首次运行建立 `since_id`；后续运行只接受更新的帖子。只有全部报告成功写入后，检查点才会提交，因此磁盘或报告错误不会让内容被误跳过。

如需同一次运行合并 GitHub 和 X，可重复传入来源：

```bash
python3 -m agent.runner \
  --source openai_codex_releases \
  --source claude_code_releases \
  --source x_frontier_ai_accounts \
  --output outputs/full-radar \
  --hours 48
```

## Cookie 过期与重新授权

先在浏览器重新登录 X、取得新的两项 Cookie，再运行：

```bash
python3 -m tools.x_twscrape setup <X用户名> --replace
python3 -m tools.x_twscrape status
```

本地账号数据库默认位于 `~/.ai-intelligence-radar/twscrape.db`，增量检查点位于同目录的 `checkpoints/`。文件权限会尽量收紧到当前用户。可用 `python3 -m tools.x_twscrape paths` 查看实际位置，也可通过 `X_TWSCRAPE_DB` 和 `RADAR_STATE_DIR` 改写路径。

## 风险与生产替代

- `twscrape` 依赖 X 的内部接口，平台变化可能导致突然失效。
- 自动访问可能触发限速、验证或账号限制；不要使用主账号，不要高频轮询。
- 本项目只保留链接、必要元数据、最多 400 字摘要和短证据，不批量复制完整帖子。
- 生产环境优先使用 X 官方 API，并通过 Secret 管理 Bearer Token。
