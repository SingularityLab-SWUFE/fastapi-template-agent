FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy repository into image. .dockerignore will exclude tests, docs and other dev files
COPY . .

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

EXPOSE 8000

RUN chmod +x ./docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
