import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.person import Person
from app.models.user import User
from app.schemas.person import PersonCreate, PersonRead, PersonUpdate

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


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonCreate, db: DbSession, current_user: CurrentUser) -> Person:
    person = Person(owner_id=current_user.id, **payload.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("", response_model=list[PersonRead])
def list_persons(db: DbSession, current_user: CurrentUser) -> list[Person]:
    return list(
        db.scalars(
            select(Person)
            .where(Person.owner_id == current_user.id)
            .order_by(Person.surname, Person.given_name, Person.id)
        )
    )


@router.get("/{person_id}", response_model=PersonRead)
def read_person(person_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Person:
    return get_owned_person(person_id=person_id, owner_id=current_user.id, db=db)


@router.patch("/{person_id}", response_model=PersonRead)
def update_person(
    person_id: uuid.UUID,
    payload: PersonUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Person:
    person = get_owned_person(person_id=person_id, owner_id=current_user.id, db=db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(person_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Response:
    person = get_owned_person(person_id=person_id, owner_id=current_user.id, db=db)
    db.delete(person)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
