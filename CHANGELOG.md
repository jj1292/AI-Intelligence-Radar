# Changelog

## [0.6.0] - 2026-07-27

- 将产品入口从“每位用户配置 X 账号”改为“维护者一次认证、所有用户订阅公开 Feed”。
- 新增滚动 RSS 2.0 和 JSON Feed 1.1 输出，支持跨运行合并、链接去重、时间排序和 200 条上限。
- 将 `write_feed` 纳入 Agent Loop；Feed 发布失败时不提交来源 Checkpoint。
- 新增 GitHub Actions 定时发布器，每日两次采集并提交公开 Feed 与非敏感 `since_id`。
- 新增 CI 环境变量授权入口，Cookie 只从 GitHub Secret 读取，缺少配置时安全跳过。
- 新增公开订阅部署文档，中英文 README 以零认证 Feed URL 为首要入口。
- 测试扩展到 42 项，覆盖 Feed 格式、滚动合并、去重和发布失败时的 Checkpoint 保护。

## [0.5.0] - 2026-07-27

- 新增实验性 `twscrape` X 采集器，支持本地 Cookie 授权、状态检查和显式重新授权。
- 新增按 `collection_mode` 分发的 Source Dispatcher，统一 GitHub Atom 与 X 采集契约。
- 新增 X Tweet 到 Intelligence Signal 的标准化、官方账号公司映射和 T2 证据边界。
- 新增 `since_id` 增量检查点；只有知识卡片、趋势雷达和 AI Pulse 日报成功写入后才提交。
- 默认运行继续只选择无需授权的来源，X 必须通过 `--source x_frontier_ai_accounts` 显式启用。
- 本地账号数据库默认保存在 `~/.ai-intelligence-radar/`，并补充 Git 忽略与文件权限保护。
- 测试扩展到 35 项，覆盖来源分发、账号来源选择、X 标准化、重新授权、增量过滤和检查点失败保护。

## [0.4.0] - 2026-07-27

- 新增 OpenAI Codex 与 Anthropic Claude Code GitHub Release Atom 真实采集器。
- 新增 48 小时时效过滤，排除旧信号和未来时间信号；原失败案例提升为通过。
- 新增 RunState、Tool Registry、确定性 Planner、最小 Agent Loop、停止条件与 JSONL Trace。
- 新增来源失败处理：全部来源失败时 Run 失败，部分失败时保留 Trace 并继续。
- 趋势判断改为至少两个独立公司/来源组合，避免同仓库连续 Release 被误判为行业趋势。
- 评测基线提升为 3/3 通过、平均 2.0/2，CI 启用 `--strict` 发布门禁。
- 新增真实运行样例：20 条官方 Release 中保留 2 条 48 小时内信号，0 个工具错误。
- 将 AI Pulse 从独立 Demo 迁移为 Agent Loop 的 `write_briefing` 输出工具，直接消费统一 Intelligence Signal。
- 清理根目录旧 AI Pulse 材料与旧新闻数据结构，新增项目演进史；Dify 调整为可选适配器。
- Markdown 成为默认可移植输出，Obsidian 调整为可选阅读端，不再与项目代码目录绑定。
- 测试扩展到 20 项，覆盖时效、Atom 解析、Loop、Trace、来源失败和趋势独立性。

## [0.3.0] - 2026-07-22

- 新增评估优先的产品升级路径：先建立当前确定性管道基线，再引入 Agent Loop。
- 新增 3 个可复现 Eval Case，覆盖正常、边界和风险场景。
- 新增 0–2 分自动评分器，评估相关性、证据、覆盖度、去重与时效、判断价值和过程可靠性。
- 新增一票否决规则、基线报告与 `--strict` 发布门禁模式。
- 当前基线为 2 个案例通过、1 个案例未通过，明确暴露 48 小时时效过滤缺口。
- GitHub Actions 现在会运行评测基线，确保报告生成链路持续可用。

## [0.2.0] - 2026-07-22

- 将项目定位从每日简报升级为 AI 行业情报与个人知识系统。
- 新增 OpenAI/Codex、Anthropic/Claude、Google/Gemini、X、Reddit 来源注册表及来源等级。
- 新增 Intelligence Signal JSON Schema、来源注册表校验器和 Obsidian 知识卡片生成器。
- 新增趋势雷达：至少两条独立信号才进入趋势候选。
- 新增 v0.2 PRD、Dify 升级蓝图、示例数据和 4 项知识库测试。
- 明确 X/Reddit 授权、数据留存、版权和凭证安全边界。

## [0.1.0] - 2026-07-22

- 新增标准项目 README、Dify 工作流升级蓝图和后续 Roadmap。
- 将筛选与排序改为基于实际输入数据执行，不再返回硬编码排名结果。
- 支持从 JSON 文件读取新闻并指定输出路径和简报日期。
- 明确演示数据与实时搜索的边界，避免把 Demo 描述成真实新闻服务。
- 新增单元测试和 GitHub Actions。
