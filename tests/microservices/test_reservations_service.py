from datetime import date, timedelta

import pytest

from src.main.python.microservices.reservations_service.app import create_app, db


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.drop_all()


def get_future_date():
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


def test_health_endpoint_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_reservation_with_valid_data(client):
    response = client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "customer_phone": "999999999",
        "guests": 4,
        "date": get_future_date(),
        "time": "20:00",
        "notes": "Mesa cerca a ventana"
    })

    data = response.get_json()

    assert response.status_code == 201
    assert data["customer_name"] == "Cliente prueba"
    assert data["status"] == "pending"


def test_create_reservation_rejects_empty_customer_name(client):
    response = client.post("/api/reservations", json={
        "customer_name": "",
        "guests": 2,
        "date": get_future_date(),
        "time": "19:00"
    })

    assert response.status_code == 400


def test_create_reservation_rejects_past_date(client):
    past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    response = client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "guests": 2,
        "date": past_date,
        "time": "19:00"
    })

    assert response.status_code == 400


def test_create_reservation_rejects_invalid_guests(client):
    response = client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "guests": 0,
        "date": get_future_date(),
        "time": "19:00"
    })

    assert response.status_code == 400


def test_list_reservations_returns_created_reservation(client):
    client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "guests": 3,
        "date": get_future_date(),
        "time": "21:00"
    })

    response = client.get("/api/reservations")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["customer_name"] == "Cliente prueba"


def test_confirm_reservation_changes_status(client):
    create_response = client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "guests": 3,
        "date": get_future_date(),
        "time": "21:00"
    })

    reservation_id = create_response.get_json()["id"]

    response = client.put(f"/api/reservations/{reservation_id}/confirm")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "confirmed"


def test_cancel_reservation_changes_status(client):
    create_response = client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "guests": 3,
        "date": get_future_date(),
        "time": "21:00"
    })

    reservation_id = create_response.get_json()["id"]

    response = client.put(f"/api/reservations/{reservation_id}/cancel")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "cancelled"


def test_delete_reservation_removes_record(client):
    create_response = client.post("/api/reservations", json={
        "customer_name": "Cliente prueba",
        "guests": 3,
        "date": get_future_date(),
        "time": "21:00"
    })

    reservation_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/api/reservations/{reservation_id}")
    list_response = client.get("/api/reservations")

    assert delete_response.status_code == 200
    assert list_response.get_json() == []
