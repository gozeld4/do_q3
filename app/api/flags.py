from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.cache import FlagCache, get_flag_cache
from app.database import get_db
from app.schemas import (
    FlagCreate,
    FlagEvaluationResponse,
    FlagResponse,
    FlagUpdate,
    OverrideResponse,
    OverrideUpsert,
    UserId,
)
from app.service import FlagService

router = APIRouter(prefix="/flags", tags=["flags"])


def get_flag_service(
    session: Annotated[Session, Depends(get_db)],
    cache: Annotated[FlagCache, Depends(get_flag_cache)],
) -> FlagService:
    return FlagService(session, cache)


Service = Annotated[FlagService, Depends(get_flag_service)]


@router.post(
    "",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flag(
    data: FlagCreate,
    response: Response,
    service: Service,
) -> object:
    flag = service.create_flag(data)
    response.headers["Location"] = f"/flags/{flag.key}"
    return flag


@router.get("", response_model=list[FlagResponse])
def list_flags(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> object:
    return service.list_flags(offset=offset, limit=limit)


@router.get("/{key}/evaluate", response_model=FlagEvaluationResponse)
def evaluate_flag(
    key: str,
    user_id: UserId,
    response: Response,
    service: Service,
) -> object:
    result, cache_hit = service.evaluate_flag(key=key, user_id=user_id)
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return {
        "flag": key,
        "user_id": user_id,
        "enabled": result.enabled,
        "reason": result.reason,
    }


@router.get("/{key}", response_model=FlagResponse)
def get_flag(key: str, service: Service) -> object:
    return service.require_flag(key)


@router.patch("/{key}", response_model=FlagResponse)
def update_flag(key: str, data: FlagUpdate, service: Service) -> object:
    return service.update_flag(key, data)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(key: str, service: Service) -> Response:
    service.delete_flag(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{key}/users/{user_id}",
    response_model=OverrideResponse,
    responses={status.HTTP_201_CREATED: {"model": OverrideResponse}},
)
def upsert_override(
    key: str,
    user_id: UserId,
    data: OverrideUpsert,
    response: Response,
    service: Service,
) -> object:
    override, created = service.upsert_override(
        key=key,
        user_id=user_id,
        enabled=data.enabled,
    )
    if created:
        response.status_code = status.HTTP_201_CREATED
    return override


@router.delete(
    "/{key}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_override(
    key: str,
    user_id: UserId,
    service: Service,
) -> Response:
    service.delete_override(key=key, user_id=user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
