from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, event
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def create_database_engine(database_url: str, **kwargs: Any) -> Engine:
    engine_options: dict[str, Any] = {"pool_pre_ping": True, **kwargs}

    if make_url(database_url).get_backend_name() == "sqlite":
        connect_args = {
            "check_same_thread": False,
            **engine_options.pop("connect_args", {}),
        }
        engine_options["connect_args"] = connect_args

    engine = sqlalchemy_create_engine(database_url, **engine_options)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_database_engine(get_settings().database_url)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
