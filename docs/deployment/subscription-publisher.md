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

### 1. 配置后台采集账号

建议使用专用 X 账号。在 GitHub 仓库进入 `Settings → Secrets and variables → Actions`：

- Repository variable：`X_ACCOUNT_USERNAME`
- Repository secret：`X_COOKIE_AUTH_TOKEN`
- Repository secret：`X_COOKIE_CT0`

Cookie 只保存在 GitHub Actions Secret 中。不要写入 Issue、README、工作流参数、日志或 Git 提交。

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
2. 动态读取 `config/subscriptions.json`，抓取启用的 GitHub Release、RSS/Atom、Reddit 社区，以及后台已授权时的 X 账号；
3. 通过 72 小时时效门并生成卡片、趋势、AI Pulse 和公开 Feed；
4. 将最多 200 条滚动 Feed 条目与公开 `since_id` 检查点提交到仓库；
5. 只有 Feed 成功写入后才推进检查点。

缺少变量或 Secret 时，工作流只跳过 X，仍会持续发布无需认证的 GitHub、RSS/Atom 和 Reddit 来源；同时不会尝试输出凭证。

## 自托管与生产替代

Fork 仓库的开发者只有在运营自己的发布器时才需要配置账号；他们的下游订阅者同样不需要认证。

`twscrape` 依赖 X 内部接口，适合低频个人实验，可能遇到接口变更、限速或账号验证。需要稳定 SLA 时，应将后台 Collector 替换为 X 官方 API；RSS/JSON 输出契约和订阅地址可以保持不变。
