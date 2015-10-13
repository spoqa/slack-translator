import pytest


@pytest.fixture
def app():
    from app import app
    return app
