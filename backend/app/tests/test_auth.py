from fastapi.testclient import TestClient
from helpers import login_user, register_user
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def test_register_user_success(client: TestClient) -> None:
    data = register_user(client)

    assert data["email"] == "tester@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_cannot_register_same_email_twice(client: TestClient) -> None:
    register_user(client, email="duplicate@example.com")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "another-password",
            "full_name": "Another User",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email уже зарегистрирован"


def test_password_is_not_stored_in_plain_text(
    client: TestClient,
    db_session: Session,
) -> None:
    password = "secret-password"
    register_user(client, email="secure@example.com", password=password)

    user = db_session.scalar(select(User).where(User.email == "secure@example.com"))

    assert user is not None
    assert user.hashed_password != password
    assert verify_password(password, user.hashed_password)


def test_login_success(client: TestClient) -> None:
    register_user(client)

    access_token = login_user(client)

    assert isinstance(access_token, str)


def test_login_with_wrong_password_returns_error(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "tester@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"


def test_me_returns_current_user_with_valid_token(client: TestClient) -> None:
    register_user(client)
    access_token = login_user(client)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "tester@example.com"
    assert data["full_name"] == "Test User"


def test_me_without_token_returns_error(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_token_form_success(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "tester@example.com", "password": "strong-password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)


def test_token_form_wrong_password_returns_401(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": "tester@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"


def test_me_with_token_from_token_endpoint(client: TestClient) -> None:
    register_user(client)

    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": "tester@example.com", "password": "strong-password"},
    )
    access_token = token_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "tester@example.com"


def test_token_form_normalizes_email_case_and_whitespace(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/v1/auth/token",
        data={"username": " Tester@Example.com ", "password": "strong-password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
