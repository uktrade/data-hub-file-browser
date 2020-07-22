import pytest

from dhfb import app


@pytest.fixture
def client():
    app.testing = True
    yield app.test_client()


@pytest.fixture
def nologin(monkeypatch):
    monkeypatch.setattr(
        'authbroker_client.is_authenticated',
        lambda: True,
    )
