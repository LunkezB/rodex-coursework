import csv
import io
import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient
from helpers import create_authorized_user, create_person, create_relationship
from sqlalchemy.orm import Session

from app.models.relationship import ParentRole, Relationship, RelationshipKind

SessionFactory = Callable[[], Session]
SOSA_CSV_HEADER = [
    "sosa_number",
    "generation",
    "person_id",
    "surname",
    "given_name",
    "patronymic",
    "sex",
    "birth_date",
    "birth_place",
    "death_date",
    "death_place",
]


def flatten_report(data: dict[str, object]) -> dict[int, dict[str, object]]:
    generations = data["generations"]
    assert isinstance(generations, list)
    return {
        person["sosa_number"]: person
        for generation in generations
        for person in generation["persons"]
    }


def generation_numbers(data: dict[str, object]) -> dict[int, list[int]]:
    generations = data["generations"]
    assert isinstance(generations, list)
    return {
        generation["generation"]: [person["sosa_number"] for person in generation["persons"]]
        for generation in generations
    }


def parse_csv_response(response) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(response.text))
    assert reader.fieldnames is not None
    return reader.fieldnames, list(reader)


def build_three_generation_family(
    client: TestClient,
    headers: dict[str, str],
) -> dict[str, dict[str, object]]:
    family = {
        "proband": create_person(client, headers, given_name="Proband"),
        "father": create_person(client, headers, given_name="Father"),
        "mother": create_person(client, headers, given_name="Mother"),
        "father_father": create_person(client, headers, given_name="FatherFather"),
        "father_mother": create_person(client, headers, given_name="FatherMother"),
        "mother_father": create_person(client, headers, given_name="MotherFather"),
        "mother_mother": create_person(client, headers, given_name="MotherMother"),
    }

    create_relationship(client, headers, family["father"]["id"], family["proband"]["id"], "father")
    create_relationship(client, headers, family["mother"]["id"], family["proband"]["id"], "mother")
    create_relationship(
        client,
        headers,
        family["father_father"]["id"],
        family["father"]["id"],
        "father",
    )
    create_relationship(
        client,
        headers,
        family["father_mother"]["id"],
        family["father"]["id"],
        "mother",
    )
    create_relationship(
        client,
        headers,
        family["mother_father"]["id"],
        family["mother"]["id"],
        "father",
    )
    create_relationship(
        client,
        headers,
        family["mother_mother"]["id"],
        family["mother"]["id"],
        "mother",
    )
    return family


def test_build_sosa_report_requires_token(client: TestClient) -> None:
    response = client.get(f"/api/v1/reports/sosa/{uuid.uuid4()}")

    assert response.status_code == 401


def test_cannot_build_sosa_report_for_other_users_proband(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="owner@example.com")
    _, other_headers = create_authorized_user(client, email="other@example.com")
    proband = create_person(client, owner_headers, given_name="Owner")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}", headers=other_headers)

    assert response.status_code == 404


def test_sosa_report_for_proband_without_parents_returns_only_number_one(
    client: TestClient,
) -> None:
    _, headers = create_authorized_user(client)
    proband = create_person(client, headers, given_name="Proband")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["proband_id"] == proband["id"]
    assert data["max_depth"] == 5
    assert generation_numbers(data) == {0: [1]}
    assert flatten_report(data)[1]["person"]["given_name"] == "Proband"
    assert data["warnings"] == []


def test_sosa_report_numbers_father_as_two(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    proband = create_person(client, headers, given_name="Proband")
    father = create_person(client, headers, given_name="Father")
    create_relationship(client, headers, father["id"], proband["id"], "father")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}", headers=headers)

    assert response.status_code == 200
    persons = flatten_report(response.json())
    assert persons[2]["person"]["id"] == father["id"]


def test_sosa_report_numbers_mother_as_three(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    proband = create_person(client, headers, given_name="Proband")
    mother = create_person(client, headers, given_name="Mother")
    create_relationship(client, headers, mother["id"], proband["id"], "mother")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}", headers=headers)

    assert response.status_code == 200
    persons = flatten_report(response.json())
    assert persons[3]["person"]["id"] == mother["id"]


def test_sosa_report_numbers_three_generations_correctly(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    family = build_three_generation_family(client, headers)

    response = client.get(f"/api/v1/reports/sosa/{family['proband']['id']}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    persons = flatten_report(data)
    assert generation_numbers(data) == {0: [1], 1: [2, 3], 2: [4, 5, 6, 7]}
    assert {number: item["person"]["given_name"] for number, item in persons.items()} == {
        1: "Proband",
        2: "Father",
        3: "Mother",
        4: "FatherFather",
        5: "FatherMother",
        6: "MotherFather",
        7: "MotherMother",
    }


def test_sosa_report_max_depth_limits_traversal(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    family = build_three_generation_family(client, headers)

    response = client.get(
        f"/api/v1/reports/sosa/{family['proband']['id']}",
        headers=headers,
        params={"max_depth": 1},
    )

    assert response.status_code == 200
    assert response.json()["max_depth"] == 1
    assert generation_numbers(response.json()) == {0: [1], 1: [2, 3]}


def test_sosa_report_warns_and_skips_unknown_parent_role(client: TestClient) -> None:
    _, headers = create_authorized_user(client)
    proband = create_person(client, headers, given_name="Proband")
    parent = create_person(client, headers, given_name="Parent")
    create_relationship(client, headers, parent["id"], proband["id"], "unknown")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert generation_numbers(data) == {0: [1]}
    assert "unknown parent_role" in data["warnings"][0]


def test_sosa_report_does_not_loop_forever_when_database_has_cycle(
    client: TestClient,
    session_factory: SessionFactory,
) -> None:
    user, headers = create_authorized_user(client)
    proband = create_person(client, headers, given_name="Proband")
    father = create_person(client, headers, given_name="Father")
    create_relationship(client, headers, father["id"], proband["id"], "father")

    db = session_factory()
    try:
        db.add(
            Relationship(
                owner_id=uuid.UUID(str(user["id"])),
                parent_id=uuid.UUID(str(proband["id"])),
                child_id=uuid.UUID(str(father["id"])),
                kind=RelationshipKind.parent_child,
                parent_role=ParentRole.father,
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        f"/api/v1/reports/sosa/{proband['id']}",
        headers=headers,
        params={"max_depth": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert generation_numbers(data) == {0: [1], 1: [2]}
    assert any("Cycle detected" in warning for warning in data["warnings"])


def test_export_sosa_csv_requires_token(client: TestClient) -> None:
    response = client.get(f"/api/v1/reports/sosa/{uuid.uuid4()}/export.csv")

    assert response.status_code == 401


def test_cannot_export_sosa_csv_for_other_users_proband(client: TestClient) -> None:
    _, owner_headers = create_authorized_user(client, email="csv-owner@example.com")
    _, other_headers = create_authorized_user(client, email="csv-other@example.com")
    proband = create_person(client, owner_headers, given_name="Owner")

    response = client.get(
        f"/api/v1/reports/sosa/{proband['id']}/export.csv",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_sosa_csv_for_proband_without_parents_contains_header_and_number_one(
    client: TestClient,
) -> None:
    _, headers = create_authorized_user(client, email="csv-single@example.com")
    proband = create_person(
        client,
        headers,
        surname=None,
        given_name="Proband",
        patronymic=None,
        birth_place=None,
        death_place=None,
    )

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}/export.csv", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    header, rows = parse_csv_response(response)
    assert header == SOSA_CSV_HEADER
    assert len(rows) == 1
    assert rows[0]["sosa_number"] == "1"
    assert rows[0]["person_id"] == proband["id"]
    assert rows[0]["surname"] == ""
    assert rows[0]["patronymic"] == ""
    assert rows[0]["birth_place"] == ""
    assert rows[0]["death_place"] == ""


def test_sosa_csv_for_three_generations_contains_expected_numbers(
    client: TestClient,
) -> None:
    _, headers = create_authorized_user(client, email="csv-three@example.com")
    family = build_three_generation_family(client, headers)

    response = client.get(
        f"/api/v1/reports/sosa/{family['proband']['id']}/export.csv",
        headers=headers,
    )

    assert response.status_code == 200
    _, rows = parse_csv_response(response)
    assert [int(row["sosa_number"]) for row in rows] == [1, 2, 3, 4, 5, 6, 7]
    assert [int(row["generation"]) for row in rows] == [0, 1, 1, 2, 2, 2, 2]


def test_sosa_csv_max_depth_one_limits_rows_to_proband_and_parents(
    client: TestClient,
) -> None:
    _, headers = create_authorized_user(client, email="csv-depth@example.com")
    family = build_three_generation_family(client, headers)

    response = client.get(
        f"/api/v1/reports/sosa/{family['proband']['id']}/export.csv",
        headers=headers,
        params={"max_depth": 1},
    )

    assert response.status_code == 200
    _, rows = parse_csv_response(response)
    assert [int(row["sosa_number"]) for row in rows] == [1, 2, 3]


def test_sosa_csv_response_contains_content_disposition_filename(
    client: TestClient,
) -> None:
    _, headers = create_authorized_user(client, email="csv-filename@example.com")
    proband = create_person(client, headers, given_name="Proband")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}/export.csv", headers=headers)

    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert f"sosa_report_{proband['id']}.csv" in disposition


def test_unknown_parent_role_does_not_appear_in_sosa_csv_as_ancestor(
    client: TestClient,
) -> None:
    _, headers = create_authorized_user(client, email="csv-unknown@example.com")
    proband = create_person(client, headers, given_name="Proband")
    parent = create_person(client, headers, given_name="Parent")
    create_relationship(client, headers, parent["id"], proband["id"], "unknown")

    response = client.get(f"/api/v1/reports/sosa/{proband['id']}/export.csv", headers=headers)

    assert response.status_code == 200
    _, rows = parse_csv_response(response)
    assert [int(row["sosa_number"]) for row in rows] == [1]
    assert rows[0]["person_id"] == proband["id"]
