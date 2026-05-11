import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship as orm_relationship

from app.models.base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    archive_reference: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500))
    reliability_comment: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    owner = orm_relationship("User")


class PersonSource(Base, TimestampMixin):
    __tablename__ = "person_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    comment: Mapped[str | None] = mapped_column(Text)

    person = orm_relationship("Person")
    source = orm_relationship("Source")


class RelationshipSource(Base, TimestampMixin):
    __tablename__ = "relationship_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    relationship_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("relationships.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    comment: Mapped[str | None] = mapped_column(Text)

    family_relationship = orm_relationship("Relationship")
    source = orm_relationship("Source")
