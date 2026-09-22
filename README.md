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
