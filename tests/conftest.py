from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.cache import flag_cache
from app.database import Base, create_database_engine, get_db
from app.main import app


@pytest.fixture(autouse=True)
def clear_flag_cache() -> Iterator[None]:
    flag_cache.clear()
    yield
    flag_cache.clear()


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    database_path = tmp_path / "api-test.db"
    engine = create_database_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    def override_get_db() -> Iterator[Session]:
        with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)

    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(tmp_path: Path) -> Iterator[Session]:
    database_path = tmp_path / "test.db"
    engine = create_database_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    with test_session() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
