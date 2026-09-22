---
name: Milestone 1 Persistence
overview: Add the database foundation for feature flags and user overrides. The app will use SQLite during local development and PostgreSQL in production, while keeping the existing health endpoint working.
todos:
  - id: config-database
    content: Add database packages and connect the app to SQLite or PostgreSQL
    status: completed
  - id: models-layers
    content: Define the database tables and add code for reading and writing their data
    status: completed
  - id: startup-docs
    content: Create tables when the app starts and document the database setup
    status: completed
  - id: persistence-tests
    content: Test database behavior and run the project checks
    status: completed
isProject: false
---

# Milestone 1: Data Model and Persistence

## 1. Add database configuration and dependencies
- Add SQLAlchemy, the PostgreSQL driver, and application-settings packages to [`requirements.txt`](/Users/s-coding-interview/Desktop/do_q3/requirements.txt).
- Add [`app/config.py`](/Users/s-coding-interview/Desktop/do_q3/app/config.py) to read the `DATABASE_URL` environment variable.
- Use `sqlite:///./feature_flags.db` when `DATABASE_URL` is not set, so the app works locally without extra setup.
- Add a short section to [`README.md`](/Users/s-coding-interview/Desktop/do_q3/README.md) explaining the local and production database settings.

## 2. Connect the application to the database
- Add [`app/database.py`](/Users/s-coding-interview/Desktop/do_q3/app/database.py).
- Create the SQLAlchemy engine and session factory in this file.
- Add a `get_db()` function that opens a database session for each request and always closes it afterward.
- Apply the SQLite-only connection settings that FastAPI needs.
- Turn on SQLite foreign-key support so deleting a flag can also delete its user overrides.
- Make the database setup reusable so tests can create their own temporary database.

## 3. Define the database tables
- Add [`app/models.py`](/Users/s-coding-interview/Desktop/do_q3/app/models.py).
- Create the `flags` table with:
  - An integer ID.
  - A unique and searchable key.
  - A description.
  - A global enabled/disabled value.
  - Created and last-updated timestamps.
- Create the `flag_overrides` table with:
  - An integer ID.
  - A link to its flag.
  - A user ID.
  - An enabled/disabled value for that user.
- Prevent the same flag and user pair from having more than one override.
- Configure deletion so removing a flag also removes all of its overrides.
- Generate timestamps in UTC in the application so SQLite and PostgreSQL behave consistently.

## 4. Separate data shapes, database work, and business rules
- Add [`app/schemas.py`](/Users/s-coding-interview/Desktop/do_q3/app/schemas.py) with the request and response shapes that the API will use in the next milestone.
- Add [`app/repository.py`](/Users/s-coding-interview/Desktop/do_q3/app/repository.py) with functions to:
  - Create, find, list, update, and delete flags.
  - Create or update a user override.
  - Find and delete a user override.
- Keep HTTP status codes and web errors out of the repository. It should only read and write database data.
- Add [`app/service.py`](/Users/s-coding-interview/Desktop/do_q3/app/service.py) as the place for business rules. It can be thin for now and grow when evaluation and caching are added.

## 5. Create the tables when the app starts
- Update [`app/main.py`](/Users/s-coding-interview/Desktop/do_q3/app/main.py) to create missing tables during FastAPI startup.
- Make sure both table models are loaded before table creation runs.
- Keep `GET /healthz` unchanged.
- Note in the README that automatic table creation is acceptable for this time-boxed project, but a production system should use Alembic migrations for safe schema changes.

## 6. Test the database behavior
- Update [`tests/conftest.py`](/Users/s-coding-interview/Desktop/do_q3/tests/conftest.py) so each database test gets a fresh temporary SQLite database.
- Add [`tests/test_repository.py`](/Users/s-coding-interview/Desktop/do_q3/tests/test_repository.py) to verify:
  - Flags can be created, found, listed, updated, and deleted.
  - User overrides can be created and updated.
  - Duplicate flag keys are rejected.
  - Duplicate overrides for the same flag and user are rejected.
  - Deleting a flag also deletes its overrides.
- Run Ruff and pytest.
- Start the app once with the default SQLite setting and confirm it creates both tables.
- Confirm local database files remain ignored by [`.gitignore`](/Users/s-coding-interview/Desktop/do_q3/.gitignore).

## Completion criteria
- Existing health test remains green.
- Starting the app creates the `flags` and `flag_overrides` tables in SQLite.
- Setting `DATABASE_URL` switches the app to PostgreSQL without code changes.
- The database prevents duplicate keys and duplicate user overrides.
- Deleting a flag also deletes its overrides.
- Database code and business logic are separated and ready for the API work in Milestone 2.