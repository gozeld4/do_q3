from __future__ import annotations

from sqlalchemy.orm import Session

from app import repository
from app.models import Flag, FlagOverride
from app.schemas import FlagCreate, FlagUpdate


class FlagService:
    def __init__(self, session: Session) -> None:
        self.session = session

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
        except Exception:
            self.session.rollback()
            raise

    def get_flag(self, key: str) -> Flag | None:
        return repository.get_flag_by_key(self.session, key)

    def list_flags(self, *, offset: int = 0, limit: int = 100) -> list[Flag]:
        return repository.list_flags(self.session, offset=offset, limit=limit)

    def update_flag(self, flag: Flag, data: FlagUpdate) -> Flag:
        changes = data.model_dump(exclude_unset=True)
        try:
            updated_flag = repository.update_flag(
                self.session,
                flag,
                description=changes.get("description"),
                enabled=changes.get("enabled"),
            )
            self.session.commit()
            return updated_flag
        except Exception:
            self.session.rollback()
            raise

    def delete_flag(self, flag: Flag) -> None:
        try:
            repository.delete_flag(self.session, flag)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

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
        flag: Flag,
        user_id: str,
        enabled: bool,
    ) -> tuple[FlagOverride, bool]:
        try:
            result = repository.upsert_override(
                self.session,
                flag=flag,
                user_id=user_id,
                enabled=enabled,
            )
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise

    def delete_override(self, override: FlagOverride) -> None:
        try:
            repository.delete_override(self.session, override)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
