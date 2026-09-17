from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models import CategoryModel, UserModel
from src.services.auth_service import hash_access_key


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def user_factory(db):
    def create_user(name="Alice", access_key="alice-secret"):
        user = UserModel(
            name=name,
            hashed_access_key=hash_access_key(access_key),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return create_user


@pytest.fixture
def category_factory(db):
    def create_category(
        user,
        name="Food",
        category_type="expense",
        icon="fas fa-tag",
        color="#123456",
    ):
        category = CategoryModel(
            user_id=user.user_id,
            name=name,
            type=category_type,
            icon=icon,
            color=color,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    return create_category


@pytest.fixture
def sample_datetime():
    return datetime(2026, 9, 17, 12, 30)


@pytest.fixture
def money():
    return lambda value: Decimal(str(value))

@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def second_user(user_factory):
    return user_factory(name="Bob", access_key="bob-secret")


@pytest.fixture
def app(db, monkeypatch):
    """Flask app wired to the same isolated in-memory database as each test."""
    from sqlalchemy.orm import sessionmaker

    import src.api.authentication as authentication_api
    import src.api.budget as budget_api
    import src.api.category as category_api
    import src.api.goals as goals_api
    import src.api.transactions as transactions_api
    import src.decorators as decorators
    import src.main as main_module

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db.get_bind(),
    )

    modules_using_session_local = (
        authentication_api,
        budget_api,
        category_api,
        goals_api,
        transactions_api,
        decorators,
        main_module,
    )

    for module in modules_using_session_local:
        monkeypatch.setattr(module, "SessionLocal", TestingSessionLocal)

    main_module.app.config.update(TESTING=True)
    return main_module.app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def authenticated_client(client, user):
    response = client.post(
        "/auth/login",
        json={"name": user.name, "access_key": "alice-secret"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def second_authenticated_client(app, second_user):
    client = app.test_client()
    response = client.post(
        "/auth/login",
        json={"name": second_user.name, "access_key": "bob-secret"},
    )
    assert response.status_code == 200
    return client
