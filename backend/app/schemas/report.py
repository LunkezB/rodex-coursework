import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.person import Sex


class SosaPersonDetailsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    surname: str | None
    given_name: str
    patronymic: str | None
    sex: Sex
    birth_date: date | None
    birth_place: str | None
    death_date: date | None
    death_place: str | None


class SosaPersonRead(BaseModel):
    sosa_number: int
    person: SosaPersonDetailsRead


class SosaGenerationRead(BaseModel):
    generation: int
    persons: list[SosaPersonRead]


class SosaReportRead(BaseModel):
    proband_id: uuid.UUID
    max_depth: int
    generations: list[SosaGenerationRead]
    warnings: list[str] = Field(default_factory=list)
