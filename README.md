# api_template

A base API project to clone. Database, cache, auth, email confirmation, file
storage and observability are already wired — you start by adding *your* bounded
context, not by rebuilding the plumbing.

**Stack:** Litestar · SQLAlchemy 2 (async) · PostgreSQL · Redis · Alembic ·
`dependency-injector` · msgspec / pydantic.

---

## Quick start

```bash
git clone <this> my-service && cd my-service
cp .env.example .env
python scripts/utils/generate_secret.py   # paste the three secrets into .env

# pick one
uv sync --group dev
poetry install --with dev
pip install -r requirements/dev.txt

alembic upgrade head
python serve.py
```

Docs: <http://localhost:8000/api/v1/docs/swagger>

Or with Docker (api + db + redis + telemetry + nginx):

```bash
docker compose up --build
```

---

## Layout

```
src/
├── config/asgi.py            the ASGI app
├── bootstrap.py              DI wiring + lifespan
└── app/
    ├── domain/               entities, aggregates, domain events, invariants
    ├── application/          commands, queries, handlers, services, ports
    ├── data_access/          ORM models, repositories, entity sources
    ├── infra/                DI containers, adapters, event bus, providers
    ├── api/                  Litestar controllers, middlewares, deps
    ├── modules/              self-contained, liftable subsystems
    │   ├── telemetry/        structured logging → Postgres + Telegram
    │   ├── filtering/        FilterSpec query params → SQL, with OpenAPI docs
    │   └── cache/            Redis client + key building
    └── shared_kernel/        types, configs, Result, errors, validation
```

### The rules this layout encodes

- **Ports live in `application/**/ports`, implementations in `infra/adapters`
  (or `infra/services`).** A directory named `ports` never contains code that
  runs; a directory named `adapters` never contains a protocol.
- **No domain logic ⇒ no aggregate.** `blob` is the worked example: an uploaded
  object has no invariants to protect, so it has a repository and a service and
  nothing else. Do not add an aggregate out of symmetry.
- **`modules/` is for subsystems with no knowledge of the domain.** They can be
  copied into another project as-is.

---

## What's included

### Identity (`/api/v1/identity`)

Email *is* the login — there is no username.

| Route | Purpose |
|---|---|
| `POST /auth/register` | create an inactive account, mail a 6-digit code |
| `POST /auth/confirm-email` | spend the code, activate |
| `POST /auth/confirm-email/resend` | reissue (rate-limited by a per-kind cooldown) |
| `POST /auth/login` | email + password → JWT pair |
| `POST /auth/refresh` | rotate the pair |
| `POST /auth/forgot-password/step1..3` | request → verify → set |
| `GET/PATCH /users/me` | own profile (the profile *is* the user row) |
| `POST /users/me/change-password` | requires the current password |
| `GET /users`, `GET /users/{id}` | list + detail, filterable |
| `POST /users/{id}/toggle-status` | enable / disable an account |

API keys (`X-Api-Key`, HMAC-signed) work alongside bearer tokens for machine
clients — see `apik_user` in `asgi.py`.

Enumeration is deliberately hard: registration, resend and password reset return
the same answer whether or not the address exists, and login gives one error for
every kind of failure.

### Blob (`/api/v1/blobs`)

Upload (multipart), list, detail, delete. Images run a small Pillow pipeline that
writes `medium` and `thumbnail` variants next to the original. Storage sits behind
`BlobStorageProto`, so swapping the local filesystem for S3/MinIO is one new
adapter and one line in `blob_di.py`.

Paths are stored **relative to the media root** (`images/<uuid>.webp`). The root
belongs to the deployment, not the row, so it can move without a data migration;
readers re-add it via `make_media_full_url`.

### Telemetry

Every request and every unhandled error becomes a structured JSON line in
`logs/`. A separate daemon (`python runner.py`) tails those files and fans them
out to a Postgres table and, optionally, Telegram. Records carry the request's
`trace_id`, so an error row and its request row correlate.

### Filtering

Declare a filter on a query model and it becomes a validated query parameter,
a compiled SQL predicate, and an OpenAPI parameter with real bounds:

```python
class UserListQuery(ListQuery, OrderingQueryMixin, metaclass=FilterMeta):
    _ordering_allowed_fields: OrderingAllowedFieldsT = {"created_at", "email"}
    search: Annotated[Optional[ATSearch], FilterSpec.string()] = None
    status: AFStatus
    created_at__rn: ATDatetimeRN
```

Bind it with `dependencies=path_bound_query(UserListQuery)` and take it as
`list_query: UserListQuery`. Litestar's reserved `query:` kwarg builds the model
from the query string **only**, so any model with a path- or body-sourced field
fails validation under it.

---

## Configuration

Every setting is `<PREFIX>_<FIELD>`, where the prefix names the config class that
owns it. There are no unprefixed variables and no per-field aliases — if you can
see a field on a config class, you already know its environment variable.

| Prefix | Class | Holds |
|---|---|---|
| `APP_` | `AppConfig` | environment, domain, timezone, secrets, CORS |
| `JWT_` | `JwtConfig` | signing key, algorithm, token lifetimes |
| `POSTGRES_` | `DatabaseConfig` | connection |
| `REDIS_` | `RedisConfig` | connection |
| `SMTP_` | `SmtpConfig` | mailer |
| `TELEMETRY_` | `TelemetryConfig` | service name, sinks, gates |
| `TELEGRAM_` | `TelegramConfig` | alert routing |

`BasePydanticConfig` owns the file/encoding/casing rules; a config subclass
declares only its `env_prefix`, because pydantic merges `model_config` across the
MRO. Adding a setting is one field — never a field plus an alias.

**Ports are host ports.** `POSTGRES_PORT` is where postgres is published on your
machine. Inside the compose network services talk on their standard ports (5432,
6379, 8000, 80), which `compose.override.yml` sets for the containers. There is no
"internal vs external port" pair to keep in sync, and the app's own listening
port is not configurable at all.

**One host, one variable.** `APP_DOMAIN` is the public host; the scheme follows
`APP_ENVIRONMENT` (http while developing, https otherwise). `AppConfig.base_url`
composes them, and `make_media_full_url` builds every media URL from that.

`JWT_SECRET_KEY` is deliberately separate from `APP_SECRET_KEY`: rotating the
token key should invalidate sessions without touching anything encrypted with the
application secret.

A group that only works complete is validated as such — setting `SMTP_HOST` without
credentials fails at startup rather than on the first confirmation email.

## Conventions

**Identifiers are UUIDv7** (`ID_T`). Time-ordered, so they index like a sequence
while staying unguessable. `uuid.uuid7()` is stdlib only on 3.14+; until then
`shared_kernel/utils/functions/uuid_funcs.py` supplies it. Aggregates are stamped
at construction, not at INSERT — a new aggregate can raise events referencing its
own id without a flush.

**Tables carry a bounded-context prefix** (`identity_user`, `blob_object`), so two
contexts never collide on a generic name. Names live in one enum:
`data_access/orm/constants/db_constants.py`.

**Results, not exceptions, for expected failures.** Handlers return
`Result[T, list[AppExceptionDetail]]`; controllers turn a failed result into an
`AppException`. Exceptions are for the unexpected.

**One transaction per handler**, opened with `async with self._uow`. Repositories
never commit.

---

## Not included, on purpose

- **Authorization.** Users authenticate; nothing checks *permissions*. There is no
  role column and no permission table — add the scheme your project actually
  needs. The seams are `get_current_user_from_request` and the controllers.
- **A task queue.** Background work runs as Litestar `BackgroundTask`. Add
  Celery/taskiq when you have a real queue to run.
- **An admin panel.**

---

## Migrations

```bash
alembic revision --autogenerate -m "add orders"
alembic upgrade head
alembic downgrade -1
```

The URL comes from `.env` through the app's `DatabaseConfig` (see
`migrations/env.py`); `alembic.ini` leaves `sqlalchemy.url` empty on purpose so
the app and its migrations can never point at different databases.

`identity_user.avatar_id` and `blob_object.created_by_id` reference each other,
so `0001` creates both tables first and adds the cross-reference afterwards. Keep
that in mind if you ever regenerate it from scratch.

## Tests

```bash
pytest
```

The suite is dependency-free — it exercises aggregates against real (unattached)
ORM instances, so `pytest` needs no database.
