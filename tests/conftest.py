import os
import sys
import tempfile
from pathlib import Path

import pytest

# Tests use a throwaway SQLite database by default. To run them against PostgreSQL:
#   TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/eway_test pytest
# (the tables in that database are dropped and recreated!)
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL") or f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["ADMIN_EMAIL"] = "admin@test.in"
os.environ["ADMIN_PASSWORD"] = "Admin@12345"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from eway.database import Base, engine  # noqa: E402
from eway import models  # noqa: E402,F401

Base.metadata.drop_all(engine)  # start from a clean schema


@pytest.fixture(scope="session")
def app():
    return main.app


@pytest.fixture()
def anon(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin(app):
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"email": "admin@test.in", "password": "Admin@12345"})
        assert r.status_code == 200, r.text
        yield c


@pytest.fixture()
def make_client(app):
    clients = []

    def factory():
        c = TestClient(app)
        c.__enter__()
        clients.append(c)
        return c

    yield factory
    for c in clients:
        c.__exit__(None, None, None)
