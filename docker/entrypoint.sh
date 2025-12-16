#!/usr/bin/env sh
set -e

# Default DB env variables (support both DB__* nested names and plain names)
DB_HOST=${DB__HOST:-${DB_HOST:-db}}
DB_PORT=${DB__PORT:-${DB_PORT:-5432}}
DB_USER=${DB__USER:-${DB_USER:-postgres}}
DB_NAME=${DB__DATABASE:-${DB_DATABASE:-appdb}}

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
# wait for postgres to be ready
for i in $(seq 1 60); do
  if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" >/dev/null 2>&1; then
    echo "Postgres is ready"
    break
  fi
  echo "Postgres not ready yet (attempt: ${i}), sleeping 1s..."
  sleep 1
done

# Run alembic migrations
echo "Running database migrations (alembic upgrade head)"

alembic upgrade head || {
  echo "alembic upgrade head failed" >&2
  exit 1
}

# Exec the container CMD
exec "$@"
