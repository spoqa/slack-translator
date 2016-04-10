import pytest
from app import app


@pytest.fixture
def fx_app_client():
    return app.test_client()


@pytest.fixture
def fx_app():
    return app
