from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    overrides: Mapped[list[FlagOverride]] = relationship(
        back_populates="flag",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class FlagOverride(Base):
    __tablename__ = "flag_overrides"
    __table_args__ = (
        UniqueConstraint("flag_id", "user_id", name="uq_flag_override_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    flag_id: Mapped[int] = mapped_column(
        ForeignKey("flags.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean)

    flag: Mapped[Flag] = relationship(back_populates="overrides")
