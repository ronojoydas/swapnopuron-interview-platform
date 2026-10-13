
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL, get_db
from app.main import app
from app.models import Base, User, UserRole
from app.security import hash_password


EXPECTED_DEVELOPMENT_DATABASE = "swapnopuron_recruitment"
TEST_DATABASE_NAME = "swapnopuron_recruitment_test"


@pytest.fixture(scope="session")
def test_engine():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")

    database_url = make_url(DATABASE_URL)

    if database_url.database != EXPECTED_DEVELOPMENT_DATABASE:
        raise RuntimeError(
            "Unexpected development database. Check backend/.env."
        )

    test_url = database_url.set(database=TEST_DATABASE_NAME)
    engine = create_engine(test_url)

    try:
        with engine.connect() as connection:
            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if actual_database != TEST_DATABASE_NAME:
            raise RuntimeError(
                "Refusing to modify an unexpected database."
            )

        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def test_session_factory(test_engine):
    # Clear test data before each test, in foreign-key-safe order.
    with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())

    return sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest.fixture
def db_session(test_session_factory):
    return test_session_factory


@pytest.fixture
def client(test_session_factory):
    def override_get_db():
        with test_session_factory() as db:
            yield db

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


@pytest.fixture
def test_interviewer(test_session_factory):
    email = "test-interviewer@example.com"
    password = "TestInterviewerPassword123!"

    with test_session_factory() as db:
        user = User(
            full_name="Test Interviewer",
            email=email,
            password_hash=hash_password(password),
            role=UserRole.INTERVIEWER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "email": email,
            "password": password,
            "user_id": user.id,
        }
