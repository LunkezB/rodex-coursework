from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models.base import Base

SessionFactory = Callable[[], Session]


@pytest.fixture()
def session_factory() -> Generator[SessionFactory, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    try:
        yield testing_session_local
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(session_factory: SessionFactory) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def db_session(session_factory: SessionFactory) -> Generator[Session, None, None]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
