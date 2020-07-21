import pytest

from dhfb import app


@pytest.fixture
def client():
    app.testing = True
    yield app.test_client()
