FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# use aliyun mirror if you need it
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy repository into image. .dockerignore will exclude tests, docs and other dev files
COPY . .

RUN uv pip install --system --no-cache .

EXPOSE 8000

RUN chmod +x ./docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
