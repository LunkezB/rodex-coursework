import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Sex(enum.StrEnum):
    male = "male"
    female = "female"
    unknown = "unknown"


class Person(Base, TimestampMixin):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    surname: Mapped[str | None] = mapped_column(String(100), index=True)
    given_name: Mapped[str] = mapped_column(String(100), index=True)
    patronymic: Mapped[str | None] = mapped_column(String(100), index=True)
    name_variants: Mapped[str | None] = mapped_column(Text)

    sex: Mapped[Sex] = mapped_column(Enum(Sex, name="sex"), default=Sex.unknown, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_place: Mapped[str | None] = mapped_column(String(255))
    death_date: Mapped[date | None] = mapped_column(Date)
    death_place: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    owner = relationship("User")
