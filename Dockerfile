FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PROJECT_DIR=/code

WORKDIR $PROJECT_DIR

# libpq + a compiler for the few wheels that still build from source.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first: this layer is cached until the requirement files change,
# so an ordinary code edit does not reinstall the world.
COPY requirements/ $PROJECT_DIR/requirements/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements/prod.txt

COPY . $PROJECT_DIR/

RUN chmod +x ${PROJECT_DIR}/scripts/*.sh \
    && mkdir -p ${PROJECT_DIR}/media ${PROJECT_DIR}/logs \
    && chmod -R 755 ${PROJECT_DIR}/media ${PROJECT_DIR}/logs

EXPOSE 8000

CMD ["./scripts/start_api.sh"]
