from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    email: str = "tester@example.com",
    password: str = "strong-password",
    full_name: str | None = "Test User",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )

    assert response.status_code == 201
    return response.json()


def login_user(
    client: TestClient,
    email: str = "tester@example.com",
    password: str = "strong-password",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    return data["access_token"]


def create_authorized_user(
    client: TestClient,
    email: str = "owner@example.com",
) -> tuple[dict[str, object], dict[str, str]]:
    user = register_user(client, email=email)
    access_token = login_user(client, email=email)
    return user, {"Authorization": f"Bearer {access_token}"}


def person_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "surname": "Ivanov",
        "given_name": "Ivan",
        "patronymic": "Ivanovich",
        "name_variants": None,
        "sex": "unknown",
        "birth_date": None,
        "birth_place": None,
        "death_date": None,
        "death_place": None,
        "notes": None,
    }
    payload.update(overrides)
    return payload


def create_person(
    client: TestClient,
    headers: dict[str, str],
    **overrides: object,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/persons",
        headers=headers,
        json=person_payload(**overrides),
    )

    assert response.status_code == 201
    return response.json()


def create_relationship(
    client: TestClient,
    headers: dict[str, str],
    parent_id: str,
    child_id: str,
    parent_role: str = "unknown",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={
            "parent_id": parent_id,
            "child_id": child_id,
            "parent_role": parent_role,
        },
    )

    assert response.status_code == 201
    return response.json()


def source_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Metric book",
        "archive_reference": "Archive 1 / Inventory 2 / File 3",
        "url": "https://example.com/source",
        "reliability_comment": None,
        "notes": None,
    }
    payload.update(overrides)
    return payload


def create_source(
    client: TestClient,
    headers: dict[str, str],
    **overrides: object,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/sources",
        headers=headers,
        json=source_payload(**overrides),
    )

    assert response.status_code == 201
    return response.json()
