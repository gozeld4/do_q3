import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import repository
from app.models import Flag, FlagOverride


def test_flag_crud(db_session: Session) -> None:
    first = repository.create_flag(
        db_session,
        key="checkout_v2",
        description="New checkout",
        enabled=False,
    )
    second = repository.create_flag(
        db_session,
        key="recommendations",
        enabled=True,
    )
    db_session.commit()

    assert first.id is not None
    assert first.created_at is not None
    assert repository.get_flag_by_key(db_session, "checkout_v2") == first
    assert repository.get_flag_by_key(db_session, "missing") is None
    assert repository.list_flags(db_session) == [first, second]
    assert repository.list_flags(db_session, offset=1, limit=1) == [second]

    repository.update_flag(
        db_session,
        first,
        description="Updated checkout",
        enabled=True,
    )
    db_session.commit()

    assert first.description == "Updated checkout"
    assert first.enabled is True

    repository.delete_flag(db_session, second)
    db_session.commit()

    assert repository.get_flag_by_key(db_session, "recommendations") is None


def test_flag_keys_are_unique(db_session: Session) -> None:
    repository.create_flag(db_session, key="checkout_v2")
    db_session.commit()

    with pytest.raises(IntegrityError):
        repository.create_flag(db_session, key="checkout_v2")

    db_session.rollback()


def test_override_upsert_updates_existing_row(db_session: Session) -> None:
    flag = repository.create_flag(db_session, key="checkout_v2")
    db_session.commit()

    override, created = repository.upsert_override(
        db_session,
        flag=flag,
        user_id="user-123",
        enabled=True,
    )
    db_session.commit()

    assert created is True
    assert override.enabled is True

    updated_override, created = repository.upsert_override(
        db_session,
        flag=flag,
        user_id="user-123",
        enabled=False,
    )
    db_session.commit()

    override_count = db_session.scalar(
        select(func.count()).select_from(FlagOverride)
    )
    assert created is False
    assert updated_override.id == override.id
    assert updated_override.enabled is False
    assert override_count == 1


def test_flag_and_user_override_pair_is_unique(db_session: Session) -> None:
    flag = repository.create_flag(db_session, key="checkout_v2")
    db_session.commit()

    db_session.add_all(
        [
            FlagOverride(flag_id=flag.id, user_id="user-123", enabled=True),
            FlagOverride(flag_id=flag.id, user_id="user-123", enabled=False),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_deleting_flag_cascades_to_overrides(db_session: Session) -> None:
    flag = repository.create_flag(db_session, key="checkout_v2")
    repository.upsert_override(
        db_session,
        flag=flag,
        user_id="user-123",
        enabled=True,
    )
    db_session.commit()

    repository.delete_flag(db_session, flag)
    db_session.commit()

    flag_count = db_session.scalar(select(func.count()).select_from(Flag))
    override_count = db_session.scalar(
        select(func.count()).select_from(FlagOverride)
    )
    assert flag_count == 0
    assert override_count == 0
