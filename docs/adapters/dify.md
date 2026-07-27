# Dify 可选适配器

Dify 不是 AI Intelligence Radar 的核心运行时，而是一种可选的可视化编排与框架对照实现。核心 Agent Harness、数据契约和评测规则保持框架无关。

## 使用场景

- 需要可视化查看节点、变量和运行结果；
- 需要托管定时任务或快速接入 Dify 插件；
- 使用同一任务对比自研 Loop 与低代码编排的能力边界；
- 向非工程角色演示来源路由、证据门和输出步骤。

## 共享契约

Dify 实现必须复用以下仓库契约：

- 来源注册表：`config/sources.json`；
- 情报信号：`schemas/intelligence-signal.schema.json`；
- 评测规则：`evals/rubric.md`；
- 输出：知识卡片、趋势雷达和 AI Pulse 日报；
- 运行证据：至少保存工具错误、输入数量、过滤数量和输出路径。

## 节点映射

| Agent Harness | Dify 节点 | 失败处理 |
| --- | --- | --- |
| `collect_source` | 来源路由 + HTTP/API 工具 | 单来源失败时记录并继续 |
| `filter_signals` | 规范化 + 时效 + 去重 | 缺 URL 或时间的数据不进入输出 |
| `write_report` | 知识卡片 + 趋势报告 | 保留结构化信号供重试 |
| `write_briefing` | AI Pulse 日报渲染 | 失败不覆盖已生成的知识卡片 |
| `stop` | 结束节点 | 输出明确的成功或失败状态 |

## 约束

1. Dify 节点不得改变 Intelligence Signal 字段语义。
2. 摘要与判断只能使用采集结果中的事实，不补写数字或能力声明。
3. T3 社区内容必须保留社区属性，不能改写成官方结论。
4. API Key、Token、OAuth 凭证只进入环境变量或 Secret。
5. 原 Dify DSL 导入前必须脱敏，并使用同一评测集回放。

## 后续工作

- 导出并脱敏原 Dify DSL；
- 将 `official_web`、X 和 Reddit 来源映射到对应节点；
- 用固定 Feed 回放比较自研 Loop 与 Dify 的正确性、可观察性、恢复能力和维护成本。
