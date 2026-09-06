#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

: "${PROJECT_DIR:?PROJECT_DIR is not set}"

cd "${PROJECT_DIR}"

mkdir -p media/images media/files logs

echo "Applying database migrations..."
alembic upgrade head

echo "Starting API on port ${SERVER_PORT:-8000}"
exec uvicorn src.config.asgi:app \
    --host 0.0.0.0 \
    --port "${SERVER_PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-1}" \
    --no-access-log
