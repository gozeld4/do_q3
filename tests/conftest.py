from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, create_database_engine
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


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
