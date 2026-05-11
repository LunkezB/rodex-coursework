import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceBase(BaseModel):
    archive_reference: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=500)
    reliability_comment: str | None = None
    notes: str | None = None

    @field_validator("archive_reference", "url", "reliability_comment", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SourceCreate(SourceBase):
    title: str = Field(min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title is required")
        return title


class SourceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    archive_reference: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=500)
    reliability_comment: str | None = None
    notes: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("title cannot be null")
        title = value.strip()
        if not title:
            raise ValueError("title is required")
        return title

    @field_validator("archive_reference", "url", "reliability_comment", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    archive_reference: str | None
    url: str | None
    reliability_comment: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PersonSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    source_id: uuid.UUID
    comment: str | None
    created_at: datetime
    updated_at: datetime


class RelationshipSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    relationship_id: uuid.UUID
    source_id: uuid.UUID
    comment: str | None
    created_at: datetime
    updated_at: datetime
