import uuid
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.person import Person
from app.models.relationship import Relationship, RelationshipKind
from app.models.user import User
from app.schemas.relationship import RelationshipCreate, RelationshipRead

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_person(person_id: uuid.UUID, owner_id: uuid.UUID, db: Session) -> Person:
    person = db.scalar(
        select(Person).where(
            Person.id == person_id,
            Person.owner_id == owner_id,
        )
    )
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Персона не найдена")
    return person


def get_owned_relationship(
    relationship_id: uuid.UUID,
    owner_id: uuid.UUID,
    db: Session,
) -> Relationship:
    relationship = db.scalar(
        select(Relationship).where(
            Relationship.id == relationship_id,
            Relationship.owner_id == owner_id,
        )
    )
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь не найдена",
        )
    return relationship


def relationship_exists(
    parent_id: uuid.UUID,
    child_id: uuid.UUID,
    owner_id: uuid.UUID,
    db: Session,
) -> bool:
    return (
        db.scalar(
            select(Relationship.id).where(
                Relationship.owner_id == owner_id,
                Relationship.parent_id == parent_id,
                Relationship.child_id == child_id,
                Relationship.kind == RelationshipKind.parent_child,
            )
        )
        is not None
    )


def child_parent_count(child_id: uuid.UUID, owner_id: uuid.UUID, db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Relationship)
        .where(
            Relationship.owner_id == owner_id,
            Relationship.child_id == child_id,
            Relationship.kind == RelationshipKind.parent_child,
        )
    )


def would_create_cycle(
    parent_id: uuid.UUID,
    child_id: uuid.UUID,
    owner_id: uuid.UUID,
    db: Session,
) -> bool:
    rows = db.execute(
        select(Relationship.parent_id, Relationship.child_id).where(
            Relationship.owner_id == owner_id,
            Relationship.kind == RelationshipKind.parent_child,
        )
    ).all()
    children_by_parent: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for existing_parent_id, existing_child_id in rows:
        children_by_parent[existing_parent_id].append(existing_child_id)

    stack = [child_id]
    visited: set[uuid.UUID] = set()
    while stack:
        current_id = stack.pop()
        if current_id == parent_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        stack.extend(children_by_parent[current_id])

    return False


@router.post("", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED)
def create_relationship(
    payload: RelationshipCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Relationship:
    if payload.parent_id == payload.child_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Родитель и ребёнок должны быть разными персонами",
        )

    get_owned_person(person_id=payload.parent_id, owner_id=current_user.id, db=db)
    get_owned_person(person_id=payload.child_id, owner_id=current_user.id, db=db)

    if relationship_exists(
        parent_id=payload.parent_id,
        child_id=payload.child_id,
        owner_id=current_user.id,
        db=db,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Связь уже существует",
        )

    if child_parent_count(child_id=payload.child_id, owner_id=current_user.id, db=db) >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У ребёнка не может быть более двух родителей",
        )

    if would_create_cycle(
        parent_id=payload.parent_id,
        child_id=payload.child_id,
        owner_id=current_user.id,
        db=db,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Связь создаст цикл",
        )

    relationship = Relationship(
        owner_id=current_user.id,
        parent_id=payload.parent_id,
        child_id=payload.child_id,
        kind=RelationshipKind.parent_child,
        parent_role=payload.parent_role,
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)
    return relationship


@router.get("", response_model=list[RelationshipRead])
def list_relationships(db: DbSession, current_user: CurrentUser) -> list[Relationship]:
    return list(
        db.scalars(
            select(Relationship)
            .where(Relationship.owner_id == current_user.id)
            .order_by(Relationship.created_at, Relationship.id)
        )
    )


@router.get("/{relationship_id}", response_model=RelationshipRead)
def read_relationship(
    relationship_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Relationship:
    return get_owned_relationship(relationship_id=relationship_id, owner_id=current_user.id, db=db)


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relationship(
    relationship_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    relationship = get_owned_relationship(
        relationship_id=relationship_id,
        owner_id=current_user.id,
        db=db,
    )
    db.delete(relationship)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
