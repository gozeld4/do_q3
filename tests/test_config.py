import pytest
from pydantic import ValidationError

from app.config import Settings


def test_postgresql_url_uses_psycopg3_driver() -> None:
    settings = Settings(
        database_url="postgresql://user:password@host:5432/database?sslmode=require"
    )

    assert settings.database_url == (
        "postgresql+psycopg://user:password@host:5432/database?sslmode=require"
    )


def test_postgres_url_uses_psycopg3_driver() -> None:
    settings = Settings(database_url="postgres://user:password@host:5432/database")

    assert settings.database_url == (
        "postgresql+psycopg://user:password@host:5432/database"
    )


def test_explicit_driver_url_is_unchanged() -> None:
    database_url = "postgresql+psycopg://user:password@host:5432/database"

    assert Settings(database_url=database_url).database_url == database_url


def test_cache_defaults_are_bounded_and_expiring() -> None:
    settings = Settings()

    assert settings.cache_ttl_seconds == 60
    assert settings.cache_max_entries == 1000


@pytest.mark.parametrize(
    "values",
    [
        {"cache_ttl_seconds": 0},
        {"cache_max_entries": 0},
    ],
)
def test_cache_settings_must_be_positive(values: dict[str, int]) -> None:
    with pytest.raises(ValidationError):
        Settings(**values)
