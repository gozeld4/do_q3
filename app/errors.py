from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FlagNotFoundError(ApplicationError):
    status_code = 404
    code = "flag_not_found"

    def __init__(self, key: str) -> None:
        super().__init__(f"Flag '{key}' was not found")


class OverrideNotFoundError(ApplicationError):
    status_code = 404
    code = "override_not_found"

    def __init__(self, key: str, user_id: str) -> None:
        super().__init__(
            f"Override for flag '{key}' and user '{user_id}' was not found"
        )


class DuplicateFlagError(ApplicationError):
    status_code = 409
    code = "duplicate_flag"

    def __init__(self, key: str) -> None:
        super().__init__(f"Flag '{key}' already exists")


class InvalidOperationError(ApplicationError):
    status_code = 422
    code = "invalid_operation"


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def application_error_handler(
    _: Request,
    exc: ApplicationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message),
    )


async def validation_error_handler(
    _: Request,
    __: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", "Request validation failed"),
    )
