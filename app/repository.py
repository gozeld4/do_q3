from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Flag, FlagOverride


def create_flag(
    session: Session,
    *,
    key: str,
    description: str = "",
    enabled: bool = False,
) -> Flag:
    flag = Flag(key=key, description=description, enabled=enabled)
    session.add(flag)
    session.flush()
    session.refresh(flag)
    return flag


def get_flag_by_key(session: Session, key: str) -> Flag | None:
    statement = select(Flag).where(Flag.key == key)
    return session.scalar(statement)


def get_flag_with_overrides(session: Session, key: str) -> Flag | None:
    statement = (
        select(Flag)
        .options(joinedload(Flag.overrides))
        .where(Flag.key == key)
    )
    return session.execute(statement).unique().scalar_one_or_none()


def list_flags(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Flag]:
    statement = select(Flag).order_by(Flag.id).offset(offset).limit(limit)
    return list(session.scalars(statement))


def update_flag(
    session: Session,
    flag: Flag,
    *,
    description: str | None = None,
    enabled: bool | None = None,
) -> Flag:
    if description is not None:
        flag.description = description
    if enabled is not None:
        flag.enabled = enabled

    session.flush()
    session.refresh(flag)
    return flag


def delete_flag(session: Session, flag: Flag) -> None:
    session.delete(flag)
    session.flush()


def get_override(
    session: Session,
    *,
    flag_id: int,
    user_id: str,
) -> FlagOverride | None:
    statement = select(FlagOverride).where(
        FlagOverride.flag_id == flag_id,
        FlagOverride.user_id == user_id,
    )
    return session.scalar(statement)


def upsert_override(
    session: Session,
    *,
    flag: Flag,
    user_id: str,
    enabled: bool,
) -> tuple[FlagOverride, bool]:
    override = get_override(session, flag_id=flag.id, user_id=user_id)
    created = override is None

    if override is None:
        override = FlagOverride(flag=flag, user_id=user_id, enabled=enabled)
        session.add(override)
    else:
        override.enabled = enabled

    session.flush()
    session.refresh(override)
    return override, created


def delete_override(session: Session, override: FlagOverride) -> None:
    session.delete(override)
    session.flush()
