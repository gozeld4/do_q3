---
name: Milestone 2 Management API
overview: "Build the management endpoints on top of the existing database layer, with strict input checks, one safe error format, correct HTTP status codes, and API-level tests. Keep the design simple: routes handle HTTP details, the service owns business outcomes, and the repository continues to handle database reads and writes."
todos:
  - id: tighten-schemas
    content: Tighten flag, patch, override, and user-ID validation
    status: completed
  - id: standardize-errors
    content: Add application errors and one HTTP error response format
    status: completed
  - id: service-outcomes
    content: Move missing-resource and duplicate-key outcomes into the service layer
    status: completed
  - id: management-routes
    content: Implement flag CRUD and per-user override routes
    status: completed
  - id: api-tests
    content: Add isolated API tests and run Ruff and pytest
    status: completed
isProject: false
---

# Milestone 2: Management API, Validation, and Status Codes

## 1. Tighten the API data shapes
- Update [`app/schemas.py`](/Users/s-coding-interview/Desktop/do_q3/app/schemas.py) rather than replacing the schemas already created in Milestone 1.
- Keep flag keys lowercase and 2–64 characters using the existing pattern; document that one-character keys are intentionally not accepted.
- Keep descriptions at 500 characters or fewer and reject extra JSON fields.
- Make `PATCH` accept only `description` and `enabled`, reject an empty body, and reject `null` values for supplied fields.
- Validate user IDs after trimming whitespace: they must be non-empty and at most 255 characters, matching the database column.
- Keep response schemas for flags and overrides so FastAPI does not accidentally expose internal fields later.

## 2. Add one safe error format
- Add [`app/errors.py`](/Users/s-coding-interview/Desktop/do_q3/app/errors.py) with small application exceptions for a missing flag, missing override, duplicate flag key, and invalid operation.
- Return every expected error in this shape: `{"error": {"code": "...", "message": "..."}}`.
- Register handlers in [`app/main.py`](/Users/s-coding-interview/Desktop/do_q3/app/main.py) for application errors and FastAPI request-validation errors.
- Map validation failures to `422`, missing resources to `404`, and duplicate flag keys to `409`; never return database messages or stack traces to clients.

## 3. Put business outcomes in the service layer
- Update [`app/service.py`](/Users/s-coding-interview/Desktop/do_q3/app/service.py) so callers receive a flag or a clear application exception instead of repeatedly checking for `None` in each route.
- Catch SQLAlchemy `IntegrityError` when creating a flag, roll back the session, and raise the duplicate-key error. Keep the existing rollback behavior for other failed writes.
- Add service methods that load-and-update or load-and-delete flags, and that upsert or delete overrides after confirming the parent flag exists.
- Return whether an override was newly created so the route can choose `201` for creation and `200` for replacement.

## 4. Add the management routes
- Add [`app/api/__init__.py`](/Users/s-coding-interview/Desktop/do_q3/app/api/__init__.py) and [`app/api/flags.py`](/Users/s-coding-interview/Desktop/do_q3/app/api/flags.py), then include the router from [`app/main.py`](/Users/s-coding-interview/Desktop/do_q3/app/main.py).
- Implement:
  - `POST /flags`: return `201`, the created flag, and `Location: /flags/{key}`.
  - `GET /flags`: accept `limit` from 1–100 and non-negative `offset`; return flags ordered by ID for stable pagination.
  - `GET /flags/{key}`: return the flag or `404`.
  - `PATCH /flags/{key}`: update only fields present in the request and return the updated flag.
  - `DELETE /flags/{key}`: delete the flag and its overrides, then return an empty `204` response.
  - `PUT /flags/{key}/users/{user_id}`: trim and validate the user ID, return `201` when created and `200` when updated.
  - `DELETE /flags/{key}/users/{user_id}`: return `404` for a missing flag or override and an empty `204` when deleted.
- Keep database access out of route functions by injecting the session and calling `FlagService`.

## 5. Add API tests
- Update [`tests/conftest.py`](/Users/s-coding-interview/Desktop/do_q3/tests/conftest.py) so API tests override `get_db()` with a fresh temporary SQLite database. This prevents tests from writing to the developer database.
- Add [`tests/test_flags_api.py`](/Users/s-coding-interview/Desktop/do_q3/tests/test_flags_api.py) covering the full happy path for flag CRUD and override create/update/delete.
- Test the important contracts: duplicate creation is `409`; missing resources are `404`; bad keys, pagination, extra fields, blank or overlong user IDs, and empty PATCH bodies are `422`; create responses include `Location`; deletes have no body; and every expected error uses the standard shape.
- Keep the existing repository and health tests passing, then run `ruff check .` and `pytest`.

## Completion criteria
- All seven management endpoints work through the service layer.
- Status codes and response headers match the Milestone 2 contract.
- Bad client input and expected database conflicts never become `500` responses.
- Failed writes roll back cleanly.
- Automated tests prove validation, error shape, CRUD behavior, override behavior, and database isolation.