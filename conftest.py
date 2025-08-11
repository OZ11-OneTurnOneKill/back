import pytest
import httpx
from app import app   # FastAPI 앱 (app/__init__.py 에 있는 app)
from tortoise.contrib.test import initializer, finalizer
from app.apis.community.common_router import post_views


@pytest.fixture(scope="session", autouse=True)
def initialize_tests():
    initializer(["app.models.community", "app.models.user", "app.models.ai"])
    yield
    finalizer()


@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def clear_post_views():
    post_views.clear()
    yield
    post_views.clear()