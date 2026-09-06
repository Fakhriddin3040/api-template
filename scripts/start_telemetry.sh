#!/usr/bin/env bash

set -o errexit
set -o nounset

: "${PROJECT_DIR:?PROJECT_DIR is not set}"

cd "${PROJECT_DIR}"

echo "Starting telemetry daemon (log_dir=${TELEMETRY_LOG_DIR:-logs})"

exec python3 runner.py
