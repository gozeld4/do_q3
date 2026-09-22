from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app import models
from app.api.flags import router as flags_router
from app.database import engine
from app.errors import (
    ApplicationError,
    application_error_handler,
    validation_error_handler,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    models.Flag.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(flags_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
