FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml setup.py README.md LICENSE ./
COPY src ./src
COPY rules ./rules
COPY jinguzhou.example.yaml ./jinguzhou.yaml

RUN pip install --no-cache-dir .

EXPOSE 8787

CMD ["jinguzhou", "gateway", "--config", "jinguzhou.yaml", "--host", "0.0.0.0"]
