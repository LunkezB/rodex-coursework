import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.person import Person
from app.models.relationship import Relationship
from app.models.source import PersonSource, RelationshipSource, Source
from app.models.user import User
from app.schemas.source import (
    PersonSourceRead,
    RelationshipSourceRead,
    SourceCreate,
    SourceRead,
    SourceUpdate,
)

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_source(source_id: uuid.UUID, owner_id: uuid.UUID, db: Session) -> Source:
    source = db.scalar(
        select(Source).where(
            Source.id == source_id,
            Source.owner_id == owner_id,
        )
    )
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Источник не найден")
    return source


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


def get_person_source_link(
    source_id: uuid.UUID,
    person_id: uuid.UUID,
    db: Session,
) -> PersonSource | None:
    return db.scalar(
        select(PersonSource).where(
            PersonSource.source_id == source_id,
            PersonSource.person_id == person_id,
        )
    )


def get_relationship_source_link(
    source_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: Session,
) -> RelationshipSource | None:
    return db.scalar(
        select(RelationshipSource).where(
            RelationshipSource.source_id == source_id,
            RelationshipSource.relationship_id == relationship_id,
        )
    )


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: DbSession, current_user: CurrentUser) -> Source:
    source = Source(owner_id=current_user.id, **payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("", response_model=list[SourceRead])
def list_sources(db: DbSession, current_user: CurrentUser) -> list[Source]:
    return list(
        db.scalars(
            select(Source)
            .where(Source.owner_id == current_user.id)
            .order_by(Source.title, Source.id)
        )
    )


@router.get("/person-links", response_model=list[PersonSourceRead])
def list_person_source_links(
    db: DbSession,
    current_user: CurrentUser,
) -> list[PersonSource]:
    return list(
        db.scalars(
            select(PersonSource)
            .join(Source, PersonSource.source_id == Source.id)
            .join(Person, PersonSource.person_id == Person.id)
            .where(
                Source.owner_id == current_user.id,
                Person.owner_id == current_user.id,
            )
            .order_by(PersonSource.created_at.desc())
        )
    )


@router.get("/relationship-links", response_model=list[RelationshipSourceRead])
def list_relationship_source_links(
    db: DbSession,
    current_user: CurrentUser,
) -> list[RelationshipSource]:
    return list(
        db.scalars(
            select(RelationshipSource)
            .join(Source, RelationshipSource.source_id == Source.id)
            .join(Relationship, RelationshipSource.relationship_id == Relationship.id)
            .where(
                Source.owner_id == current_user.id,
                Relationship.owner_id == current_user.id,
            )
            .order_by(RelationshipSource.created_at.desc())
        )
    )


@router.get("/{source_id}", response_model=SourceRead)
def read_source(source_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Source:
    return get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)


@router.patch("/{source_id}", response_model=SourceRead)
def update_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Source:
    source = get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Response:
    source = get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)
    db.delete(source)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{source_id}/persons/{person_id}",
    response_model=PersonSourceRead,
    status_code=status.HTTP_201_CREATED,
)
def link_source_to_person(
    source_id: uuid.UUID,
    person_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> PersonSource:
    get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)
    get_owned_person(person_id=person_id, owner_id=current_user.id, db=db)

    if get_person_source_link(source_id=source_id, person_id=person_id, db=db) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Источник уже привязан к этой персоне",
        )

    link = PersonSource(source_id=source_id, person_id=person_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.delete(
    "/{source_id}/persons/{person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_source_from_person(
    source_id: uuid.UUID,
    person_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)
    get_owned_person(person_id=person_id, owner_id=current_user.id, db=db)

    link = get_person_source_link(source_id=source_id, person_id=person_id, db=db)
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Привязка источника к персоне не найдена",
        )

    db.delete(link)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{source_id}/relationships/{relationship_id}",
    response_model=RelationshipSourceRead,
    status_code=status.HTTP_201_CREATED,
)
def link_source_to_relationship(
    source_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> RelationshipSource:
    get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)
    get_owned_relationship(relationship_id=relationship_id, owner_id=current_user.id, db=db)

    if (
        get_relationship_source_link(
            source_id=source_id,
            relationship_id=relationship_id,
            db=db,
        )
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Источник уже привязан к этой связи",
        )

    link = RelationshipSource(source_id=source_id, relationship_id=relationship_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.delete(
    "/{source_id}/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_source_from_relationship(
    source_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    get_owned_source(source_id=source_id, owner_id=current_user.id, db=db)
    get_owned_relationship(relationship_id=relationship_id, owner_id=current_user.id, db=db)

    link = get_relationship_source_link(
        source_id=source_id,
        relationship_id=relationship_id,
        db=db,
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Привязка источника к связи не найдена",
        )

    db.delete(link)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
