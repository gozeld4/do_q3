# Feature Flags API

A FastAPI service for storing feature flags, applying per-user overrides, and
evaluating whether a feature is enabled.

## Database setup

The application reads its database connection from `DATABASE_URL`.

- Local development defaults to `sqlite:///./feature_flags.db`.
- Production should set `DATABASE_URL` to a PostgreSQL connection string, such
  as `postgresql+psycopg://user:password@host:5432/database`.

No database setup is required for a local run. The application creates missing
tables at startup:

```bash
uvicorn app.main:app --reload
```

To select another database:

```bash
DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/feature_flags" \
  uvicorn app.main:app --reload
```

Do not commit database credentials or `.env` files.

## Evaluate a flag

Evaluate a flag for one user with:

```bash
curl "http://localhost:8000/flags/checkout_v2/evaluate?user_id=user-123"
```

The response reports the effective state and where it came from:

```json
{
  "flag": "checkout_v2",
  "user_id": "user-123",
  "enabled": true,
  "reason": "user_override"
}
```

A user override takes priority when one exists. Otherwise, the response uses
the flag's global state and returns `global` as the reason.

## Evaluation cache

Evaluation snapshots are kept in a bounded in-process cache. By default, an
entry expires after 60 seconds and the cache holds at most 1,000 flags. These
values can be changed with `CACHE_TTL_SECONDS` and `CACHE_MAX_ENTRIES`.

The service removes a flag's cached snapshot after a successful flag update or
delete and after an override is created, updated, or deleted. The TTL is a
safety net; explicit invalidation normally makes writes visible immediately.
Evaluation responses include `X-Cache: HIT` or `X-Cache: MISS` for diagnostics.

Each application process has its own cache. If the service runs with multiple
workers or replicas, one process can briefly hold old data after another
process writes. A scaled deployment should use Redis or Valkey with pub/sub or
version-based cross-process invalidation.

## Current schema

- `flags` stores each flag's key, description, global state, and timestamps.
- `flag_overrides` stores an enabled or disabled value for one flag and user.
- A flag key must be unique.
- A flag can have only one override per user.
- Deleting a flag also deletes its user overrides.

## Schema changes

This time-boxed implementation uses SQLAlchemy's `create_all()` at startup.
That creates missing tables but does not safely update existing tables. A
production service should use versioned Alembic migrations and apply them as a
separate deployment step.

## Tests

```bash
ruff check .
pytest
```
