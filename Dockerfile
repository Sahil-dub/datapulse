FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN pip install --no-cache-dir .

CMD ["python", "-c", "from datapulse.health import get_health; print(get_health())"]