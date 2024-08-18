import re

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_execute_command():
    data = {
        "ip": "192.168.0.1",
        "command": "show ip interface brief",
        "username": "admin",
        "password": "password",
    }
    response = client.post("/execute-command/", json=data)
    assert response.status_code == 200
    assert "job_id" in response.json()
    assert re.match(r"\d+", response.json()["job_id"])
