from fastapi.testclient import TestClient
from helpers import create_authorized_user, create_person


def test_list_persons_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/persons")

    assert response.status_code == 401


def test_create_person(client: TestClient) -> None:
    user, headers = create_authorized_user(client)

    data = create_person(
        client,
        headers,
        name_variants="John Ivanov",
        sex="male",
        birth_date="1900-01-01",
        birth_place="Moscow",
        notes="Initial note",
    )

    assert data["owner_id"] == user["id"]
    assert data["surname"] == "Ivanov"
    assert data["given_name"] == "Ivan"
    assert data["sex"] == "male"
    assert data["birth_date"] == "1900-01-01"
    assert "id" in data


def test_list_persons_returns_only_current_user_persons(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    first = create_person(client, owner_headers, given_name="Ivan")
    second = create_person(client, owner_headers, given_name="Petr")
    create_person(client, other_headers, given_name="Other")

    response = client.get("/api/v1/persons", headers=owner_headers)

    assert response.status_code == 200
    data = response.json()
    assert {item["id"] for item in data} == {first["id"], second["id"]}


def test_read_own_person(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    person = create_person(client, headers)

    response = client.get(f"/api/v1/persons/{person['id']}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == person["id"]
    assert data["given_name"] == "Ivan"


def test_update_own_person(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    person = create_person(client, headers)

    response = client.patch(
        f"/api/v1/persons/{person['id']}",
        headers=headers,
        json={"surname": "Petrov", "birth_place": None, "notes": "Updated note"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["surname"] == "Petrov"
    assert data["birth_place"] is None
    assert data["notes"] == "Updated note"


def test_delete_own_person(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    person = create_person(client, headers)

    delete_response = client.delete(f"/api/v1/persons/{person['id']}", headers=headers)
    read_response = client.get(f"/api/v1/persons/{person['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_cannot_read_other_users_person(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    person = create_person(client, owner_headers)

    response = client.get(f"/api/v1/persons/{person['id']}", headers=other_headers)

    assert response.status_code == 404


def test_cannot_update_other_users_person(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    person = create_person(client, owner_headers)

    update_response = client.patch(
        f"/api/v1/persons/{person['id']}",
        headers=other_headers,
        json={"surname": "Changed"},
    )
    owner_read_response = client.get(f"/api/v1/persons/{person['id']}", headers=owner_headers)

    assert update_response.status_code == 404
    assert owner_read_response.status_code == 200
    assert owner_read_response.json()["surname"] == "Ivanov"


def test_cannot_delete_other_users_person(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    person = create_person(client, owner_headers)

    delete_response = client.delete(f"/api/v1/persons/{person['id']}", headers=other_headers)
    owner_read_response = client.get(f"/api/v1/persons/{person['id']}", headers=owner_headers)

    assert delete_response.status_code == 404
    assert owner_read_response.status_code == 200
    assert owner_read_response.json()["id"] == person["id"]
