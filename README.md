# Feature Flags API

A FastAPI service for storing feature flags, applying per-user overrides, and
evaluating whether a feature is enabled for a given user. Evaluations are
served through a bounded in-process cache.

The request lifecycle, data model, and cache design are described in
[docs/architecture.md](docs/architecture.md), including the architecture flow
diagram.

## Project layout

```text
app/
  main.py         FastAPI app, startup table creation, /healthz
  api/flags.py    HTTP routes, status codes, response headers
  schemas.py      Request and response models with input validation
  service.py      Business rules, transactions, cache invalidation
  evaluation.py   Pure override-or-global evaluation rule
  cache.py        Thread-safe TTL cache of per-flag snapshots
  repository.py   SQLAlchemy queries
  models.py       flags and flag_overrides tables
  database.py     Engine and per-request session
  config.py       Settings read from environment variables
  errors.py       Application errors and the JSON error shape
tests/            pytest suite
docs/             Architecture documentation
```

## Setup

Requires Python 3.12, which matches CI and the Docker image. Python 3.9 or
newer also works for local development.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Run locally

```bash
uvicorn app.main:app --reload
```

The service listens on `http://localhost:8000`. Interactive API documentation
(Swagger UI) is available at `http://localhost:8000/docs`, and a health check
at `http://localhost:8000/healthz`.

No database setup is required. The application uses a local SQLite file,
`feature_flags.db`, and creates missing tables at startup. Delete that file to
start with an empty database.

## Configuration

Settings are read from environment variables or a local `.env` file.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./feature_flags.db` | Database connection string |
| `CACHE_TTL_SECONDS` | `60` | Seconds before a cached flag snapshot expires |
| `CACHE_MAX_ENTRIES` | `1000` | Maximum number of flags held in the cache |

To use PostgreSQL:

```bash
DATABASE_URL="postgresql://user:password@localhost:5432/feature_flags" \
  uvicorn app.main:app --reload
```

URLs beginning with `postgres://` or `postgresql://` are converted to the
`postgresql+psycopg://` driver format automatically, so a managed database
connection string can be used as provided.

Do not commit database credentials or `.env` files.

## API

| Method | Path | Purpose | Success status |
| --- | --- | --- | --- |
| `POST` | `/flags` | Create a flag | `201`, with a `Location` header |
| `GET` | `/flags?limit=&offset=` | List flags, ordered by ID | `200` |
| `GET` | `/flags/{key}` | Get one flag | `200` |
| `PATCH` | `/flags/{key}` | Change the description, global state, or both | `200` |
| `DELETE` | `/flags/{key}` | Delete a flag and its overrides | `204` |
| `PUT` | `/flags/{key}/users/{user_id}` | Create or replace a user override | `201` if created, `200` if replaced |
| `DELETE` | `/flags/{key}/users/{user_id}` | Remove a user override | `204` |
| `GET` | `/flags/{key}/evaluate?user_id=` | Evaluate a flag for a user | `200`, with an `X-Cache` header |
| `GET` | `/healthz` | Health check | `200` |

`limit` defaults to 100 and accepts 1–100; `offset` defaults to 0.

### Validation rules

- Flag keys are 2–64 characters of lowercase letters, digits, underscores, or
  hyphens, and must start with a letter or digit.
- Descriptions are at most 500 characters.
- User IDs are trimmed, cannot be blank, and are at most 255 characters.
- Unknown JSON fields are rejected.
- A `PATCH` body must contain at least one field, and supplied values cannot be
  `null`.

### Errors

Expected errors return a consistent JSON body:

```json
{
  "error": {
    "code": "flag_not_found",
    "message": "Flag 'checkout_v2' was not found"
  }
}
```

| Status | Code | When |
| --- | --- | --- |
| `404` | `flag_not_found` | The flag does not exist |
| `404` | `override_not_found` | The user has no override for the flag |
| `409` | `duplicate_flag` | A flag with the same key already exists |
| `422` | `validation_error` | The request body, path, or query is invalid |

Failed database writes are rolled back. Internal database messages and stack
traces are not returned to clients.

## Evaluation

A user override takes priority when one exists, even when its value is
`false`. Otherwise, the flag's global state is used.

```bash
curl "http://localhost:8000/flags/checkout_v2/evaluate?user_id=user-123"
```

```json
{
  "flag": "checkout_v2",
  "user_id": "user-123",
  "enabled": true,
  "reason": "user_override"
}
```

`reason` is `user_override` or `global`.

## Evaluation cache

Evaluation snapshots are kept in a bounded in-process cache. By default, an
entry expires after 60 seconds and the cache holds at most 1,000 flags.

The service removes a flag's cached snapshot after a successful flag update or
delete and after an override is created, updated, or deleted. The TTL is a
safety net; explicit invalidation normally makes writes visible immediately.
Missing flags are not cached. Evaluation responses include `X-Cache: HIT` or
`X-Cache: MISS` for diagnostics.

Each application process has its own cache. If the service runs with multiple
workers or replicas, one process can briefly hold old data after another
process writes. A scaled deployment should use Redis or Valkey with pub/sub or
version-based cross-process invalidation.

## Example walkthrough

With the service running, the following requests show creation, caching,
override precedence, invalidation, and error handling:

```bash
B=http://localhost:8000

# Create a globally disabled flag: 201 with a Location header
curl -i -X POST $B/flags -H 'Content-Type: application/json' \
  -d '{"key":"checkout_v2","description":"New checkout","enabled":false}'

# First evaluation is a cache MISS, the repeat is a HIT; reason is "global"
curl -i "$B/flags/checkout_v2/evaluate?user_id=alice"
curl -i "$B/flags/checkout_v2/evaluate?user_id=alice"

# Enable the flag for alice only: 201, and the cached snapshot is invalidated
curl -i -X PUT $B/flags/checkout_v2/users/alice \
  -H 'Content-Type: application/json' -d '{"enabled":true}'

# alice gets true via "user_override"; bob still gets the global value
curl -i "$B/flags/checkout_v2/evaluate?user_id=alice"
curl -i "$B/flags/checkout_v2/evaluate?user_id=bob"

# Enable the flag globally
curl -i -X PATCH $B/flags/checkout_v2 \
  -H 'Content-Type: application/json' -d '{"enabled":true}'

# Errors: 409 duplicate, 422 invalid key, 404 missing flag
curl -i -X POST $B/flags -H 'Content-Type: application/json' -d '{"key":"checkout_v2"}'
curl -i -X POST $B/flags -H 'Content-Type: application/json' -d '{"key":"BAD KEY"}'
curl -i $B/flags/missing
```

## Tests

```bash
ruff check .
pytest --cov=app --cov-report=term-missing
```

The suite covers repository CRUD, unique keys and overrides, cascade deletion,
API validation, status codes, headers and error shapes, override precedence in
both directions, and cache hits, misses, and invalidation. Each test uses a
fresh temporary SQLite database and an empty cache.

## Docker

```bash
docker build -t feature-flags .
docker run --rm -p 8080:8080 feature-flags
```

The container runs as a non-root user and listens on `$PORT`, defaulting to
`8080`. Pass `-e DATABASE_URL=...` to use PostgreSQL; without it, the container
uses a SQLite file that is lost when the container is removed.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull
request. It installs dependencies on Python 3.12, runs Ruff, runs pytest with
coverage, and builds the Docker image.

## Deployment

The service currently runs locally. The Docker image and `DATABASE_URL`
handling are prepared for DigitalOcean App Platform with a managed PostgreSQL
database, but that deployment has not been completed. The intended steps are:

1. Create an App Platform app from this repository using the Dockerfile.
2. Attach a managed PostgreSQL database and set `DATABASE_URL` to its
   connection string.
3. Use `/healthz` as the health check path.

## Current schema

- `flags` stores each flag's key, description, global state, and timestamps.
- `flag_overrides` stores an enabled or disabled value for one flag and user.
- A flag key must be unique.
- A flag can have only one override per user.
- Deleting a flag also deletes its user overrides.

## Schema changes and limitations

This time-boxed implementation uses SQLAlchemy's `create_all()` at startup.
That creates missing tables but does not safely update existing tables. A
production service should use versioned Alembic migrations and apply them as a
separate deployment step.

Authentication and authorization are not implemented. A production management
API should restrict who can create or change flags.
