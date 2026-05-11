import enum
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RelationshipKind(enum.StrEnum):
    parent_child = "parent_child"


class ParentRole(enum.StrEnum):
    father = "father"
    mother = "mother"
    unknown = "unknown"


class Relationship(Base, TimestampMixin):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", "kind", name="uq_relationship_parent_child_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), index=True
    )

    kind: Mapped[RelationshipKind] = mapped_column(
        Enum(RelationshipKind, name="relationship_kind"), default=RelationshipKind.parent_child
    )
    parent_role: Mapped[ParentRole] = mapped_column(
        Enum(ParentRole, name="parent_role"), default=ParentRole.unknown
    )

    owner = relationship("User")
    parent = relationship("Person", foreign_keys=[parent_id])
    child = relationship("Person", foreign_keys=[child_id])
