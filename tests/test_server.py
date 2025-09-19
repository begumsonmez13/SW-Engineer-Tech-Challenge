import os
import tempfile
import pytest
from fastapi.testclient import TestClient
import server

@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    # Create a temporary DB file
    fd, path = tempfile.mkstemp()
    os.close(fd)

    # Point server.DB_PATH to our temp file
    monkeypatch.setattr(server, "DB_PATH", path)
    server.init_db()

    yield path

    os.remove(path)

def test_insert_and_get_series(temp_db):
    """
    Test inserting a series and retrieving it by SeriesInstanceUID.
    """
    client = TestClient(server.app)

    # Example payload
    payload = {
        "SeriesInstanceUID": "1.2.3.4",
        "PatientID": "123",
        "PatientName": "Doe^John",
        "StudyInstanceUID": "0.0.0.0",
        "NumInstances": 5,
    }

    # Insert series
    r = client.post("/series", json=payload)
    assert r.status_code == 200

    # Fetch by UID
    r = client.get("/series/1.2.3.4")
    assert r.status_code == 200
    data = r.json()
    assert data["PatientID"] == "123"
    assert data["PatientName"] == "Doe^John"
    assert data["StudyInstanceUID"] == "0.0.0.0"
    assert data["NumInstances"] == 5


