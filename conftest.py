import pytest
import asyncio
from tortoise.contrib.test import finalizer, initializer

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def initialize_tests():
    """Initialize test database."""
    initializer(["app.models"], db_url="sqlite://:memory:")
    yield
    finalizer()

@pytest.fixture
def anyio_backend():
    return "asyncio"