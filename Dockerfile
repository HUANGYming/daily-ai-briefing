FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the application and the approved source allow-list into an immutable image.
COPY pyproject.toml README.md ./
COPY src ./src
COPY config/sources.yaml ./config/sources.yaml
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 briefing
USER briefing

ENTRYPOINT ["python", "-m", "ai_briefing"]
CMD ["--config", "/app/config/sources.yaml"]
