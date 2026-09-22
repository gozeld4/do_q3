from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import repository
from app.cache import FlagCache, FlagSnapshot
from app.errors import (
    DuplicateFlagError,
    FlagNotFoundError,
    OverrideNotFoundError,
)
from app.evaluation import EvaluationResult
from app.evaluation import evaluate_flag as evaluate_snapshot
from app.models import Flag, FlagOverride
from app.schemas import FlagCreate, FlagUpdate


class FlagService:
    def __init__(self, session: Session, cache: FlagCache) -> None:
        self.session = session
        self.cache = cache

    def create_flag(self, data: FlagCreate) -> Flag:
        try:
            flag = repository.create_flag(
                self.session,
                key=data.key,
                description=data.description,
                enabled=data.enabled,
            )
            self.session.commit()
            return flag
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateFlagError(data.key) from exc
        except Exception:
            self.session.rollback()
            raise

    def get_flag(self, key: str) -> Flag | None:
        return repository.get_flag_by_key(self.session, key)

    def require_flag(self, key: str) -> Flag:
        flag = self.get_flag(key)
        if flag is None:
            raise FlagNotFoundError(key)
        return flag

    def list_flags(self, *, offset: int = 0, limit: int = 100) -> list[Flag]:
        return repository.list_flags(self.session, offset=offset, limit=limit)

    def evaluate_flag(
        self,
        *,
        key: str,
        user_id: str,
    ) -> tuple[EvaluationResult, bool]:
        snapshot = self.cache.get(key)
        cache_hit = snapshot is not None

        if snapshot is None:
            flag = repository.get_flag_with_overrides(self.session, key)
            if flag is None:
                raise FlagNotFoundError(key)
            snapshot = FlagSnapshot(
                global_enabled=flag.enabled,
                overrides={
                    override.user_id: override.enabled
                    for override in flag.overrides
                },
            )
            self.cache.set(key, snapshot)

        result = evaluate_snapshot(
            global_enabled=snapshot.global_enabled,
            override_enabled=snapshot.overrides.get(user_id),
        )
        return result, cache_hit

    def update_flag(self, key: str, data: FlagUpdate) -> Flag:
        flag = self.require_flag(key)
        changes = data.model_dump(exclude_unset=True)
        try:
            updated_flag = repository.update_flag(
                self.session,
                flag,
                description=changes.get("description"),
                enabled=changes.get("enabled"),
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.cache.invalidate(key)
        return updated_flag

    def delete_flag(self, key: str) -> None:
        flag = self.require_flag(key)
        try:
            repository.delete_flag(self.session, flag)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.cache.invalidate(key)

    def get_override(
        self,
        *,
        flag_id: int,
        user_id: str,
    ) -> FlagOverride | None:
        return repository.get_override(
            self.session,
            flag_id=flag_id,
            user_id=user_id,
        )

    def upsert_override(
        self,
        *,
        key: str,
        user_id: str,
        enabled: bool,
    ) -> tuple[FlagOverride, bool]:
        flag = self.require_flag(key)
        try:
            result = repository.upsert_override(
                self.session,
                flag=flag,
                user_id=user_id,
                enabled=enabled,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.cache.invalidate(key)
        return result

    def delete_override(self, *, key: str, user_id: str) -> None:
        flag = self.require_flag(key)
        override = self.get_override(flag_id=flag.id, user_id=user_id)
        if override is None:
            raise OverrideNotFoundError(key, user_id)

        try:
            repository.delete_override(self.session, override)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.cache.invalidate(key)
