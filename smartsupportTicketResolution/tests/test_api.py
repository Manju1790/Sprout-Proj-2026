import os
import tempfile
import pytest

import database


@pytest.fixture
def client(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)

    monkeypatch.setattr(database, "DB_PATH", path)
    database.init_db()

    from app import app
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    os.unlink(path)


def sample_ticket():
    return {
        "name": "Manju",
        "email": "user@example.com",
        "subject": "Payment failed",
        "description": "My payment failed and money was deducted."
    }


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_analyze(client):
    response = client.post(
        "/api/tickets/analyze",
        json={
            "subject": "Payment failed",
            "description": "Money was deducted but order failed."
        }
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["category"] == "Payment"
    assert data["team"] == "Billing"


def test_create_ticket(client):
    response = client.post(
        "/api/tickets",
        json=sample_ticket()
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["category"] == "Payment"
    assert data["status"] == "Open"


def test_filter_and_status(client):
    created = client.post(
        "/api/tickets",
        json=sample_ticket()
    ).get_json()

    response = client.patch(
        f"/api/tickets/{created['id']}/status",
        json={"status": "Resolved"}
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "Resolved"

    response = client.get("/api/tickets?status=Resolved")
    assert len(response.get_json()) == 1


def test_invalid_ticket(client):
    response = client.post(
        "/api/tickets",
        json={"name": "Test"}
    )

    assert response.status_code == 400
