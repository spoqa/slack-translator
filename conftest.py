import pytest


@pytest.fixture
def fx_app():
    from app import app, cache
    return app
