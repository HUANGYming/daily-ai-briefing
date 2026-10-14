"""Airflow DAG for the internal daily AI briefing.

Airflow setup (secrets are deliberately not stored in this repository):
  - Connection `qwen_onprem`: host=your internal gateway host, password=service token,
    extra={"scheme":"https", "path":"/v1", "model":"Qwen3.8-Next"}
  - Connection `ai_briefing_smtp`: host, port, login, password, extra={"from":"..."}
  - Variable `AI_BRIEFING_RECIPIENTS`: JSON list of internal distribution addresses
  - Variable `AI_BRIEFING_CONFIG_PATH`: absolute path to approved sources.yaml on the worker
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.models import Variable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _inject_runtime_secrets() -> None:
    qwen = BaseHook.get_connection("qwen_onprem")
    smtp = BaseHook.get_connection("ai_briefing_smtp")
    qwen_extra = qwen.extra_dejson
    smtp_extra = smtp.extra_dejson
    if not qwen.host or not qwen.password:
        raise ValueError("qwen_onprem must include a host and service-token password")
    if not smtp.host or not smtp.login or not smtp.password:
        raise ValueError("ai_briefing_smtp must include host, login, and password")
    scheme = qwen_extra.get("scheme", "https")
    path = str(qwen_extra.get("path", "/v1")).strip("/")
    qwen_port = f":{qwen.port}" if qwen.port else ""
    os.environ["QWEN_BASE_URL"] = f"{scheme}://{qwen.host}{qwen_port}/{path}"
    os.environ["QWEN_API_KEY"] = str(qwen.password)
    os.environ["QWEN_MODEL"] = qwen_extra.get("model", "Qwen3.8-Next")
    os.environ["SMTP_HOST"] = smtp.host
    os.environ["SMTP_PORT"] = str(smtp.port or 587)
    os.environ["SMTP_USER"] = str(smtp.login)
    os.environ["SMTP_PASSWORD"] = str(smtp.password)
    os.environ["SMTP_FROM"] = smtp_extra.get("from", smtp.login)
    recipients = Variable.get("AI_BRIEFING_RECIPIENTS", deserialize_json=True)
    if not isinstance(recipients, list) or not all(isinstance(value, str) for value in recipients):
        raise ValueError("AI_BRIEFING_RECIPIENTS must be a JSON array of email addresses")
    os.environ["AI_BRIEFING_RECIPIENTS"] = ",".join(recipients)


@dag(
    dag_id="daily_ai_briefing",
    description="Public AI intelligence digest for internal AI team",
    schedule="0 8 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Macau"),
    catchup=False,
    default_args={"owner": "ai-in-house", "retries": 2, "retry_delay": timedelta(minutes=10)},
    max_active_runs=1,
    tags=["ai", "internal", "email"],
)
def daily_ai_briefing():
    @task
    def generate_and_send() -> int:
        _inject_runtime_secrets()
        from ai_briefing.pipeline import run

        config_path = Variable.get("AI_BRIEFING_CONFIG_PATH")
        return run(config_path)

    generate_and_send()


daily_ai_briefing()
