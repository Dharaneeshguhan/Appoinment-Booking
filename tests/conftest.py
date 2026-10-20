import os
import tempfile
import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, init_db, get_connection


@pytest.fixture
def temp_db_file():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def client(temp_db_file):
    def override_get_db():
        conn = get_connection(temp_db_file)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
