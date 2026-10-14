# AI 每日情报（内部版）

面向内部 AI in-house 团队的工作日 AI 情报邮件：从经批准的公开 RSS/Atom 来源收集候选，由部署在内网的 **Qwen3.8-Next** 生成英文摘要、技术价值筛选和业务启发，再经企业 SMTP 投递给团队。Airflow 负责定时、重试和运行记录。

## 设计边界

- 模型网关、服务密钥、收件人和 SMTP 凭据只存在于 Airflow Connections/Variables 或部署环境，绝不提交到仓库。
- 输入仅限安全团队批准的公开源。程序不会上传内部运营数据、客户/会员资料、交易数据或赌场业务策略。
- Prompt 将外部文章视为不可信内容，忽略其中的指令；邮件中提供原文链接，摘要不取代来源核验。
- “团队参考”仅用于识别企业技术评估方向（例如知识助手、运维、数据安全）；不产生博彩策略、玩家画像、法律或监管建议。

## 快速开始

```bash
cd /Users/huangyiming/Desktop/code/daily-ai-briefing
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp config/sources.example.yaml config/sources.yaml
cp .env.example .env  # 填内网 Qwen 和测试 SMTP；.env 不会被 Git 跟踪
set -a; source .env; set +a
python -m ai_briefing --config config/sources.yaml --dry-run
pytest
```

`--dry-run` 会真实读取批准的公开源并调用内网模型，但**永不发送邮件**。如需纯配置校验，请运行 `pytest`。

## Airflow 部署

将仓库安装到 Airflow worker 的 Python 环境，并将 `dags/daily_ai_briefing.py` 放入 DAGs 路径（或建立软链接）。在 Airflow 中创建：

| 对象 | 名称 | 必填内容 |
| --- | --- | --- |
| Connection | `qwen_onprem` | host=内网 Qwen 网关；password=服务令牌；extra：`{"scheme":"https","path":"/v1","model":"Qwen3.8-Next"}` |
| Connection | `ai_briefing_smtp` | 企业 SMTP host/port/login/password；extra：`{"from":"ai-briefing@internal.example"}` |
| Variable | `AI_BRIEFING_RECIPIENTS` | JSON 数组，例如 `["ai-team@internal.example"]` |
| Variable | `AI_BRIEFING_CONFIG_PATH` | worker 上已审核的 `sources.yaml` 绝对路径 |

默认排程是澳门时间工作日 08:00（DAG 明确设定为 `Asia/Macau` 时区）。DAG 使用 `max_active_runs=1` 并在失败时重试两次，避免重复并发投递。

## 上线前检查

1. 由信息安全/法务确认 RSS allow-list、邮件分发组与保留策略。
2. 确认 Qwen gateway 是仅限内网的 OpenAI-compatible endpoint，且日志不会记录完整请求或服务令牌。
3. 先在 Airflow 以测试收件人手动触发一次，检查链接、英文摘要和 SMTP 审计记录。
4. 再解除 DAG 的暂停状态；日常变更通过审核后的 `sources.yaml` 完成。
