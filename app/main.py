from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models
from app.database import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    models.Flag.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
