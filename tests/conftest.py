import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from datetime import datetime

from hw3.demo_service.api.main import create_app
from hw3.demo_service.core.users import UserService, UserInfo, UserRole
from hw3.demo_service.core.users import password_is_longer_than_8
from hw3.demo_service.api.utils import initialize


async def to_str_async[_TVal](x: _TVal) -> str:
    return str(x)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def app() -> FastAPI:
    app_instance = create_app()
    return app_instance


@pytest.fixture(scope="module")
def test_client(app: FastAPI):
    return TestClient(app)


@pytest.fixture(scope="module")
async def async_client():
    app = create_app()
    async with initialize(app):
        yield app


@pytest.fixture(scope="module", autouse=True)
def initialize_user_service(app: FastAPI):
    user_service = UserService(
        password_validators=[
            password_is_longer_than_8,
            lambda pwd: any(char.isdigit() for char in pwd),
        ]
    )
    user_service.register(
        UserInfo(
            username="admin",
            name="admin",
            birthdate=datetime.fromtimestamp(0.0),
            role=UserRole.ADMIN,
            password="superSecretAdminPassword123",
        )
    )
    app.state.user_service = user_service


@pytest.fixture(scope="module")
def user_service(app: FastAPI) -> UserService:
    if not hasattr(app.state, "user_service"):
        raise RuntimeError("UserService is not initialized in app.state")
    return app.state.user_service
