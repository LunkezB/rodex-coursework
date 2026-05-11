import csv
import io
import uuid
from collections import defaultdict, deque
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.person import Person
from app.models.relationship import ParentRole, Relationship, RelationshipKind
from app.models.user import User
from app.schemas.report import (
    SosaGenerationRead,
    SosaPersonDetailsRead,
    SosaPersonRead,
    SosaReportRead,
)
from app.services.sosa import PersonNode, build_sosa_report

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
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


@router.get("/sosa-demo")
def demo_sosa_report() -> list[dict[str, object]]:
    """Демо-роспись без БД. Нужна, чтобы проверить алгоритм и форму ответа API."""
    persons = {
        "p1": PersonNode(id="p1", full_name="Пробанд"),
        "p2": PersonNode(id="p2", full_name="Отец пробанда"),
        "p3": PersonNode(id="p3", full_name="Мать пробанда"),
        "p4": PersonNode(id="p4", full_name="Дед по отцу"),
        "p5": PersonNode(id="p5", full_name="Бабушка по отцу"),
    }
    parents_by_child = {
        "p1": ("p2", "p3"),
        "p2": ("p4", "p5"),
    }

    report = build_sosa_report(
        proband_id="p1",
        persons=persons,
        parents_by_child=parents_by_child,
        max_depth=3,
    )
    return [item.model_dump() for item in report]


@router.get("/sosa/{proband_id}", response_model=SosaReportRead)
def read_sosa_report(
    proband_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    max_depth: Annotated[int, Query(ge=0)] = 5,
) -> SosaReportRead:
    return build_owned_db_sosa_report(
        proband_id=proband_id,
        db=db,
        current_user=current_user,
        max_depth=max_depth,
    )


@router.get("/sosa/{proband_id}/export.csv")
def export_sosa_report_csv(
    proband_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    max_depth: Annotated[int, Query(ge=0)] = 5,
) -> Response:
    report = build_owned_db_sosa_report(
        proband_id=proband_id,
        db=db,
        current_user=current_user,
        max_depth=max_depth,
    )
    return Response(
        content=sosa_report_to_csv(report),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="sosa_report_{proband_id}.csv"'},
    )


def build_owned_db_sosa_report(
    *,
    proband_id: uuid.UUID,
    db: Session,
    current_user: User,
    max_depth: int,
) -> SosaReportRead:
    proband = db.scalar(
        select(Person).where(
            Person.id == proband_id,
            Person.owner_id == current_user.id,
        )
    )
    if proband is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Персона не найдена")

    persons = {
        person.id: person
        for person in db.scalars(select(Person).where(Person.owner_id == current_user.id))
    }
    relationships = list(
        db.scalars(
            select(Relationship)
            .where(
                Relationship.owner_id == current_user.id,
                Relationship.kind == RelationshipKind.parent_child,
            )
            .order_by(Relationship.created_at, Relationship.id)
        )
    )

    return build_db_sosa_report(
        proband=proband,
        persons=persons,
        relationships=relationships,
        max_depth=max_depth,
    )


def sosa_report_to_csv(report: SosaReportRead) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(SOSA_CSV_HEADER)

    rows = sorted(
        (
            (generation.generation, person)
            for generation in report.generations
            for person in generation.persons
        ),
        key=lambda item: (item[0], item[1].sosa_number),
    )
    for generation, item in rows:
        person = item.person
        writer.writerow(
            [
                item.sosa_number,
                generation,
                person.id,
                person.surname,
                person.given_name,
                person.patronymic,
                person.sex.value,
                person.birth_date,
                person.birth_place,
                person.death_date,
                person.death_place,
            ]
        )

    return output.getvalue()


def build_db_sosa_report(
    *,
    proband: Person,
    persons: dict[uuid.UUID, Person],
    relationships: list[Relationship],
    max_depth: int,
) -> SosaReportRead:
    parents_by_child: dict[uuid.UUID, list[Relationship]] = defaultdict(list)
    for relationship in relationships:
        parents_by_child[relationship.child_id].append(relationship)

    warnings: list[str] = []
    seen_warnings: set[str] = set()

    def add_warning(message: str) -> None:
        if message not in seen_warnings:
            warnings.append(message)
            seen_warnings.add(message)

    items_by_generation: dict[int, list[SosaPersonRead]] = defaultdict(list)
    queue: deque[tuple[uuid.UUID, int, int, tuple[uuid.UUID, ...]]] = deque(
        [(proband.id, 1, 0, ())]
    )

    while queue:
        person_id, sosa_number, generation, path = queue.popleft()

        if person_id in path:
            cycle_path = " -> ".join(str(path_id) for path_id in (*path, person_id))
            add_warning(f"Cycle detected in ancestry path: {cycle_path}; branch skipped.")
            continue

        person = persons.get(person_id)
        if person is None:
            add_warning(f"Person {person_id} is outside the current user's data; branch skipped.")
            continue

        items_by_generation[generation].append(
            SosaPersonRead(
                sosa_number=sosa_number,
                person=SosaPersonDetailsRead.model_validate(person),
            )
        )

        if generation >= max_depth:
            continue

        next_path = (*path, person_id)
        assigned_roles: set[ParentRole] = set()

        for relationship in parents_by_child.get(person_id, []):
            if relationship.parent_role == ParentRole.unknown:
                add_warning(
                    "Relationship "
                    f"{relationship.id} has unknown parent_role for child {relationship.child_id}; "
                    "parent was not assigned a Sosa number."
                )
                continue

            if relationship.parent_role in assigned_roles:
                add_warning(
                    "Multiple "
                    f"{relationship.parent_role.value} relationships for child "
                    f"{relationship.child_id}; parent {relationship.parent_id} was skipped."
                )
                continue

            assigned_roles.add(relationship.parent_role)
            parent_number = (
                sosa_number * 2
                if relationship.parent_role == ParentRole.father
                else sosa_number * 2 + 1
            )

            if relationship.parent_id in next_path:
                cycle_path = " -> ".join(
                    str(path_id) for path_id in (*next_path, relationship.parent_id)
                )
                add_warning(f"Cycle detected in ancestry path: {cycle_path}; branch skipped.")
                continue

            queue.append((relationship.parent_id, parent_number, generation + 1, next_path))

    generations = [
        SosaGenerationRead(
            generation=generation,
            persons=sorted(items, key=lambda item: item.sosa_number),
        )
        for generation, items in sorted(items_by_generation.items())
    ]

    return SosaReportRead(
        proband_id=proband.id,
        max_depth=max_depth,
        generations=generations,
        warnings=warnings,
    )
