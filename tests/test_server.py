import os
import tempfile
import sqlite3
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
    client = TestClient(server.app)

    # Prepare payload
    payload = {
        "SeriesInstanceUID": "1.2.3.4",
        "PatientID": "123",
        "PatientName": "Doe^John",
        "StudyInstanceUID": "9.9.9.9",
        "NumInstances": 5,
    }

    # Insert series
    r = client.post("/series", json=payload)
    assert r.status_code == 200
    assert r.json()["message"] == "Series inserted"

    # Fetch by UID
    r = client.get("/series/1.2.3.4")
    assert r.status_code == 200
    data = r.json()
    assert data["PatientID"] == "123"
    assert data["NumInstances"] == 5

def test_list_series(temp_db):
    client = TestClient(server.app)

    # Insert multiple
    payloads = [
        {
            "SeriesInstanceUID": f"uid{i}",
            "PatientID": f"pid{i}",
            "PatientName": f"Name^{i}",
            "StudyInstanceUID": f"study{i}",
            "NumInstances": i,
        }
        for i in range(3)
    ]
    for p in payloads:
        client.post("/series", json=p)

    r = client.get("/series")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 3
    assert rows[0]["SeriesInstanceUID"].startswith("uid")  # last inserted first
