from fastapi.testclient import TestClient
from helpers import create_authorized_user, create_person, create_relationship


def test_list_relationships_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/relationships")

    assert response.status_code == 401


def test_create_parent_child_relationship_between_own_persons(client: TestClient) -> None:
    user, headers = create_authorized_user(client)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")

    response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"parent_id": parent["id"], "child_id": child["id"], "parent_role": "father"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["owner_id"] == user["id"]
    assert data["parent_id"] == parent["id"]
    assert data["child_id"] == child["id"]
    assert data["kind"] == "parent_child"
    assert data["parent_role"] == "father"


def test_cannot_create_relationship_with_other_users_person(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    parent = create_person(client, owner_headers, given_name="Parent")
    other_child = create_person(client, other_headers, given_name="Other")

    response = client.post(
        "/api/v1/relationships",
        headers=owner_headers,
        json={"parent_id": parent["id"], "child_id": other_child["id"]},
    )

    assert response.status_code == 404


def test_cannot_create_relationship_from_person_to_same_person(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    person = create_person(client, headers)

    response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"parent_id": person["id"], "child_id": person["id"]},
    )

    assert response.status_code == 400


def test_cannot_create_duplicate_relationship(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    create_relationship(client, headers, parent["id"], child["id"])

    response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"parent_id": parent["id"], "child_id": child["id"]},
    )

    assert response.status_code == 409


def test_cannot_create_more_than_two_parents_for_child(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    first_parent = create_person(client, headers, given_name="First")
    second_parent = create_person(client, headers, given_name="Second")
    third_parent = create_person(client, headers, given_name="Third")
    child = create_person(client, headers, given_name="Child")
    create_relationship(client, headers, first_parent["id"], child["id"])
    create_relationship(client, headers, second_parent["id"], child["id"])

    response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"parent_id": third_parent["id"], "child_id": child["id"]},
    )

    assert response.status_code == 400


def test_cannot_create_cycle(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    first = create_person(client, headers, given_name="A")
    second = create_person(client, headers, given_name="B")
    third = create_person(client, headers, given_name="C")
    create_relationship(client, headers, first["id"], second["id"])
    create_relationship(client, headers, second["id"], third["id"])

    response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"parent_id": third["id"], "child_id": first["id"]},
    )

    assert response.status_code == 400


def test_list_relationships_returns_own_relationships(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    first_parent = create_person(client, headers, given_name="First")
    second_parent = create_person(client, headers, given_name="Second")
    child = create_person(client, headers, given_name="Child")
    first_relationship = create_relationship(client, headers, first_parent["id"], child["id"])
    second_relationship = create_relationship(client, headers, second_parent["id"], child["id"])

    response = client.get("/api/v1/relationships", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert {item["id"] for item in data} == {
        first_relationship["id"],
        second_relationship["id"],
    }


def test_cannot_see_other_users_relationships(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    parent = create_person(client, owner_headers, given_name="Parent")
    child = create_person(client, owner_headers, given_name="Child")
    create_relationship(client, owner_headers, parent["id"], child["id"])

    response = client.get("/api/v1/relationships", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_read_own_relationship(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    relationship = create_relationship(client, headers, parent["id"], child["id"])

    response = client.get(f"/api/v1/relationships/{relationship['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == relationship["id"]


def test_cannot_read_other_users_relationship(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    parent = create_person(client, owner_headers, given_name="Parent")
    child = create_person(client, owner_headers, given_name="Child")
    relationship = create_relationship(client, owner_headers, parent["id"], child["id"])

    response = client.get(f"/api/v1/relationships/{relationship['id']}", headers=other_headers)

    assert response.status_code == 404


def test_delete_own_relationship(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    relationship = create_relationship(client, headers, parent["id"], child["id"])

    delete_response = client.delete(f"/api/v1/relationships/{relationship['id']}", headers=headers)
    read_response = client.get(f"/api/v1/relationships/{relationship['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_cannot_delete_other_users_relationship(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    parent = create_person(client, owner_headers, given_name="Parent")
    child = create_person(client, owner_headers, given_name="Child")
    relationship = create_relationship(client, owner_headers, parent["id"], child["id"])

    delete_response = client.delete(
        f"/api/v1/relationships/{relationship['id']}",
        headers=other_headers,
    )
    owner_read_response = client.get(
        f"/api/v1/relationships/{relationship['id']}",
        headers=owner_headers,
    )

    assert delete_response.status_code == 404
    assert owner_read_response.status_code == 200
    assert owner_read_response.json()["id"] == relationship["id"]
