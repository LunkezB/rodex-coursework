from fastapi.testclient import TestClient
from helpers import create_authorized_user, create_person, create_relationship, create_source


def test_list_sources_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/sources")

    assert response.status_code == 401


def test_create_source(client: TestClient) -> None:
    user, headers = create_authorized_user(client)

    data = create_source(
        client,
        headers,
        title="Birth record",
        archive_reference="Fond 1 / Opis 2 / Delo 3",
        reliability_comment="Original record",
        notes="Readable scan",
    )

    assert data["owner_id"] == user["id"]
    assert data["title"] == "Birth record"
    assert data["archive_reference"] == "Fond 1 / Opis 2 / Delo 3"
    assert data["reliability_comment"] == "Original record"
    assert data["notes"] == "Readable scan"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_sources_returns_own_sources(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    first = create_source(client, headers, title="First")
    second = create_source(client, headers, title="Second")

    response = client.get("/api/v1/sources", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert {item["id"] for item in data} == {first["id"], second["id"]}


def test_cannot_see_other_users_sources(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    create_source(client, owner_headers)

    response = client.get("/api/v1/sources", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_read_own_source(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers, title="Revision list")

    response = client.get(f"/api/v1/sources/{source['id']}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == source["id"]
    assert data["title"] == "Revision list"


def test_cannot_read_other_users_source(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers)

    response = client.get(f"/api/v1/sources/{source['id']}", headers=other_headers)

    assert response.status_code == 404


def test_update_own_source(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)

    response = client.patch(
        f"/api/v1/sources/{source['id']}",
        headers=headers,
        json={"title": "Updated source", "archive_reference": None, "notes": "Updated note"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated source"
    assert data["archive_reference"] is None
    assert data["notes"] == "Updated note"


def test_cannot_update_other_users_source(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers, title="Owner source")

    update_response = client.patch(
        f"/api/v1/sources/{source['id']}",
        headers=other_headers,
        json={"title": "Changed"},
    )
    owner_read_response = client.get(f"/api/v1/sources/{source['id']}", headers=owner_headers)

    assert update_response.status_code == 404
    assert owner_read_response.status_code == 200
    assert owner_read_response.json()["title"] == "Owner source"


def test_delete_own_source(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)

    delete_response = client.delete(f"/api/v1/sources/{source['id']}", headers=headers)
    read_response = client.get(f"/api/v1/sources/{source['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_cannot_delete_other_users_source(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers)

    delete_response = client.delete(f"/api/v1/sources/{source['id']}", headers=other_headers)
    owner_read_response = client.get(f"/api/v1/sources/{source['id']}", headers=owner_headers)

    assert delete_response.status_code == 404
    assert owner_read_response.status_code == 200
    assert owner_read_response.json()["id"] == source["id"]


def test_link_source_to_own_person(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    person = create_person(client, headers)

    response = client.post(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source_id"] == source["id"]
    assert data["person_id"] == person["id"]
    assert data["comment"] is None


def test_cannot_link_same_source_to_same_person_twice(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    person = create_person(client, headers)
    create_response = client.post(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )

    duplicate_response = client.post(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )

    assert create_response.status_code == 201
    assert duplicate_response.status_code == 409


def test_cannot_link_source_to_other_users_person(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers)
    other_person = create_person(client, other_headers)

    response = client.post(
        f"/api/v1/sources/{source['id']}/persons/{other_person['id']}",
        headers=owner_headers,
    )

    assert response.status_code == 404


def test_cannot_link_other_users_source_to_own_person(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    other_source = create_source(client, other_headers)
    person = create_person(client, owner_headers)

    response = client.post(
        f"/api/v1/sources/{other_source['id']}/persons/{person['id']}",
        headers=owner_headers,
    )

    assert response.status_code == 404


def test_unlink_source_from_person(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    person = create_person(client, headers)
    create_response = client.post(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )

    delete_response = client.delete(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )
    second_delete_response = client.delete(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )

    assert create_response.status_code == 201
    assert delete_response.status_code == 204
    assert second_delete_response.status_code == 404


def test_link_source_to_own_relationship(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    relationship = create_relationship(client, headers, parent["id"], child["id"])

    response = client.post(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source_id"] == source["id"]
    assert data["relationship_id"] == relationship["id"]
    assert data["comment"] is None


def test_cannot_link_same_source_to_same_relationship_twice(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    relationship = create_relationship(client, headers, parent["id"], child["id"])
    create_response = client.post(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )

    duplicate_response = client.post(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )

    assert create_response.status_code == 201
    assert duplicate_response.status_code == 409


def test_cannot_link_source_to_other_users_relationship(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers)
    parent = create_person(client, other_headers, given_name="Parent")
    child = create_person(client, other_headers, given_name="Child")
    other_relationship = create_relationship(client, other_headers, parent["id"], child["id"])

    response = client.post(
        f"/api/v1/sources/{source['id']}/relationships/{other_relationship['id']}",
        headers=owner_headers,
    )

    assert response.status_code == 404


def test_cannot_link_other_users_source_to_own_relationship(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    other_source = create_source(client, other_headers)
    parent = create_person(client, owner_headers, given_name="Parent")
    child = create_person(client, owner_headers, given_name="Child")
    relationship = create_relationship(client, owner_headers, parent["id"], child["id"])

    response = client.post(
        f"/api/v1/sources/{other_source['id']}/relationships/{relationship['id']}",
        headers=owner_headers,
    )

    assert response.status_code == 404


def test_unlink_source_from_relationship(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    relationship = create_relationship(client, headers, parent["id"], child["id"])
    create_response = client.post(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )

    delete_response = client.delete(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )
    second_delete_response = client.delete(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )

    assert create_response.status_code == 201
    assert delete_response.status_code == 204
    assert second_delete_response.status_code == 404


def test_list_person_links_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/sources/person-links")

    assert response.status_code == 401


def test_list_person_links_empty(client: TestClient) -> None:
    _, headers = create_authorized_user(client)

    response = client.get("/api/v1/sources/person-links", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_person_links_returns_own_links(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    person = create_person(client, headers)
    link_response = client.post(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=headers,
    )

    response = client.get("/api/v1/sources/person-links", headers=headers)

    assert link_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source_id"] == source["id"]
    assert data[0]["person_id"] == person["id"]


def test_cannot_see_other_users_person_links(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers)
    person = create_person(client, owner_headers)
    client.post(
        f"/api/v1/sources/{source['id']}/persons/{person['id']}",
        headers=owner_headers,
    )

    response = client.get("/api/v1/sources/person-links", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_relationship_links_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/sources/relationship-links")

    assert response.status_code == 401


def test_list_relationship_links_empty(client: TestClient) -> None:
    _, headers = create_authorized_user(client)

    response = client.get("/api/v1/sources/relationship-links", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_relationship_links_returns_own_links(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    source = create_source(client, headers)
    parent = create_person(client, headers, given_name="Parent")
    child = create_person(client, headers, given_name="Child")
    relationship = create_relationship(client, headers, parent["id"], child["id"])
    link_response = client.post(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=headers,
    )

    response = client.get("/api/v1/sources/relationship-links", headers=headers)

    assert link_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source_id"] == source["id"]
    assert data[0]["relationship_id"] == relationship["id"]


def test_cannot_see_other_users_relationship_links(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    source = create_source(client, owner_headers)
    parent = create_person(client, owner_headers, given_name="Parent")
    child = create_person(client, owner_headers, given_name="Child")
    relationship = create_relationship(client, owner_headers, parent["id"], child["id"])
    client.post(
        f"/api/v1/sources/{source['id']}/relationships/{relationship['id']}",
        headers=owner_headers,
    )

    response = client.get("/api/v1/sources/relationship-links", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []
