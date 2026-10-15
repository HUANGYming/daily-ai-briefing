"""Run one immutable Daily AI Intelligence container from Airflow.

The application dependencies stay inside the image. Airflow needs only the Docker
provider, access to the Docker daemon, Connections for Qwen/SMTP, and Variables.
No secret is baked into the image or DAG source.
"""
from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.exceptions import AirflowNotFoundException
from airflow.hooks.base import BaseHook
from airflow.models import Variable
from airflow.providers.docker.operators.docker import DockerOperator

IMAGE = Variable.get("AI_BRIEFING_IMAGE")
DOCKER_NETWORK = Variable.get("AI_BRIEFING_DOCKER_NETWORK", default_var="bridge")


def _runtime_environment() -> dict[str, str]:
    """Resolve credentials only when the task starts; never template or log them."""
    smtp = BaseHook.get_connection("ai_briefing_smtp")
    if not smtp.host or not smtp.login or not smtp.password:
        raise ValueError("ai_briefing_smtp requires host, login, and password")
    recipients = Variable.get("AI_BRIEFING_RECIPIENTS", deserialize_json=True)
    if not isinstance(recipients, list) or not all(isinstance(value, str) for value in recipients):
        raise ValueError("AI_BRIEFING_RECIPIENTS must be a JSON array of email addresses")
    environment = {
        "QWEN_BASE_URL": Variable.get("AI_BRIEFING_QWEN_BASE_URL"),
        "QWEN_MODEL": Variable.get("AI_BRIEFING_QWEN_MODEL", default_var="Qwen3.8-Next"),
        "SMTP_HOST": str(smtp.host),
        "SMTP_PORT": str(smtp.port or 587),
        "SMTP_USER": str(smtp.login),
        "SMTP_PASSWORD": str(smtp.password),
        "SMTP_FROM": str(smtp.extra_dejson.get("from", smtp.login)),
        "AI_BRIEFING_RECIPIENTS": ",".join(recipients),
    }
    try:
        tavily = BaseHook.get_connection("tavily")
    except AirflowNotFoundException:
        # The image gives a clear runtime error only if its search config is enabled.
        pass
    else:
        if tavily.password:
            environment["TAVILY_API_KEY"] = str(tavily.password)
    try:
        brave = BaseHook.get_connection("brave")
    except AirflowNotFoundException:
        pass
    else:
        if brave.password:
            environment["BRAVE_SEARCH_API_KEY"] = str(brave.password)
    return environment


class InternalBriefingDockerOperator(DockerOperator):
    """Inject Connection secrets into the container without exposing template values."""

    def execute(self, context):
        self.private_environment = _runtime_environment()
        return super().execute(context)

with DAG(
    dag_id="daily_ai_briefing",
    description="Public AI intelligence digest for internal AI team",
    schedule="0 8 * * 1-5",
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Macau"),
    catchup=False,
    default_args={"owner": "ai-in-house", "retries": 2, "retry_delay": timedelta(minutes=10)},
    max_active_runs=1,
    tags=["ai", "internal", "docker", "email"],
) as dag:
    run_briefing = InternalBriefingDockerOperator(
        task_id="generate_and_send",
        image=IMAGE,
        command=["--config", "/app/config/sources.yaml"],
        docker_conn_id="docker_default",
        auto_remove="success",
        mount_tmp_dir=False,
        force_pull=False,
        network_mode=DOCKER_NETWORK,
        execution_timeout=timedelta(minutes=20),
    )
