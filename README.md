# AI 每日情报（内部版）

面向内部 AI in-house 团队的工作日 AI 情报邮件：从经批准的公开 RSS/Atom 来源收集候选，由部署在内网的 **Qwen3.8-Next** 生成英文摘要、技术价值筛选和业务启发，再经企业 SMTP 投递给团队。每次发布构建一个不可变 Docker image；Airflow 只负责运行指定 image、定时、重试和运行记录。

## 设计边界

- 模型网关地址、收件人、SMTP 凭据、Tavily/Brave key 只存在于 Airflow Connections/Variables 或部署环境，绝不提交到仓库。当前 vLLM 无认证部署不需要模型令牌。
- 输入仅限安全团队批准的公开源。程序不会上传内部运营数据、客户/会员资料、交易数据或赌场业务策略。
- Prompt 将外部文章视为不可信内容，忽略其中的指令；邮件中提供原文链接，摘要不取代来源核验。
- “团队参考”仅用于识别企业技术评估方向（例如知识助手、运维、数据安全）；不产生博彩策略、玩家画像、法律或监管建议。
- Tavily 与 Brave 只接收预设的公开 AI 新闻查询；不要将内部项目名、运营数据、客户/会员信息或业务策略放进查询词。

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

## 镜像构建与发布

`config/sources.yaml` 会被打包进镜像，因此每个 image 都包含确定版本的代码和数据源 allow-list。不要把凭据放进该文件。

```bash
make image IMAGE=registry.internal.example/ai/daily-ai-briefing TAG=2026.10.14-1
make push  IMAGE=registry.internal.example/ai/daily-ai-briefing TAG=2026.10.14-1
```

使用不可变 tag（例如发布编号或 commit SHA），不要复用 `latest`。镜像运行时需要访问内网 Qwen、企业 SMTP 和批准的 RSS 来源。

## Airflow 部署

Airflow worker 只需安装 `apache-airflow-providers-docker` 并可访问 Docker daemon（通常挂载 `/var/run/docker.sock`）；不需要安装本项目的 Python 依赖。将 [DAG 文件](dags/daily_ai_briefing.py) 放入 Airflow 的 DAGs 路径。在 Airflow 中创建：

| 对象 | 名称 | 必填内容 |
| --- | --- | --- |
| Connection | `docker_default` | 指向 Airflow worker 可访问的 Docker daemon |
| Connection | `ai_briefing_smtp` | 企业 SMTP host/port/login/password；extra：`{"from":"ai-briefing@internal.example"}` |
| Connection | `tavily` | password=Tavily API key；缺失时自动跳过 Tavily，继续使用其他来源 |
| Connection | `brave` | password=Brave Search API key；缺失时自动跳过 Brave，继续使用其他来源 |
| Variable | `AI_BRIEFING_IMAGE` | 完整、不可变 image tag，例如 `registry.internal.example/ai/daily-ai-briefing:2026.10.14-1` |
| Variable | `AI_BRIEFING_QWEN_BASE_URL` | vLLM 的完整 OpenAI-compatible endpoint，必须以 `/v1` 结尾，例如 `http://qwen-vllm.internal:8000/v1` |
| Variable | `AI_BRIEFING_QWEN_MODEL` | vLLM 的 `--served-model-name`；默认 `Qwen3.8-Next` |
| Variable | `AI_BRIEFING_RECIPIENTS` | JSON 数组，例如 `["ai-team@internal.example"]` |
| Variable | `AI_BRIEFING_DOCKER_NETWORK` | 可选；Docker 网络名，默认 `bridge`。内网服务需使用可达网络。 |

默认排程是澳门时间工作日 08:00（DAG 明确设定为 `Asia/Macau` 时区）。DAG 使用 `max_active_runs=1` 并在失败时重试两次，避免重复并发投递。`auto_remove="success"` 会在成功后删除容器；失败容器会保留，便于排查。

搜索服务按“尽力而为”运行：Tavily 或 Brave 缺少 key、超时或返回错误时，会在日志记录 warning 并自动退回另一家搜索服务或 RSS-only 日报，不会阻断邮件。

## 上线前检查

1. 由信息安全/法务确认 RSS allow-list、邮件分发组与保留策略。
2. 确认 vLLM endpoint 仅限内网可达；即使当前无认证，也应通过 Docker 网络策略限制访问范围。
3. 先在 Airflow 以测试收件人手动触发一次，检查 Docker task 日志、双搜索源去重后的链接、英文摘要和 SMTP 审计记录。
4. 将新 image tag 写入 `AI_BRIEFING_IMAGE`，再解除 DAG 的暂停状态。日常数据源或代码变更必须构建并发布新 image。
