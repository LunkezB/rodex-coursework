import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.person import Sex


class PersonBase(BaseModel):
    surname: str | None = Field(default=None, max_length=100)
    patronymic: str | None = Field(default=None, max_length=100)
    name_variants: str | None = None
    sex: Sex = Sex.unknown
    birth_date: date | None = None
    birth_place: str | None = Field(default=None, max_length=255)
    death_date: date | None = None
    death_place: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator(
        "surname",
        "patronymic",
        "name_variants",
        "birth_place",
        "death_place",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PersonCreate(PersonBase):
    given_name: str = Field(min_length=1, max_length=100)

    @field_validator("given_name")
    @classmethod
    def normalize_given_name(cls, value: str) -> str:
        given_name = value.strip()
        if not given_name:
            raise ValueError("Имя обязательно")
        return given_name


class PersonUpdate(BaseModel):
    surname: str | None = Field(default=None, max_length=100)
    given_name: str | None = Field(default=None, min_length=1, max_length=100)
    patronymic: str | None = Field(default=None, max_length=100)
    name_variants: str | None = None
    sex: Sex | None = None
    birth_date: date | None = None
    birth_place: str | None = Field(default=None, max_length=255)
    death_date: date | None = None
    death_place: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator("given_name")
    @classmethod
    def normalize_given_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Имя не может быть пустым")
        given_name = value.strip()
        if not given_name:
            raise ValueError("Имя обязательно")
        return given_name

    @field_validator(
        "surname",
        "patronymic",
        "name_variants",
        "birth_place",
        "death_place",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    surname: str | None
    given_name: str
    patronymic: str | None
    name_variants: str | None
    sex: Sex
    birth_date: date | None
    birth_place: str | None
    death_date: date | None
    death_place: str | None
    notes: str | None
