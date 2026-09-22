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
