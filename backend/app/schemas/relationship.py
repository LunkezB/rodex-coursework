import uuid

from pydantic import BaseModel, ConfigDict

from app.models.relationship import ParentRole, RelationshipKind


class RelationshipCreate(BaseModel):
    parent_id: uuid.UUID
    child_id: uuid.UUID
    parent_role: ParentRole = ParentRole.unknown


class RelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    parent_id: uuid.UUID
    child_id: uuid.UUID
    kind: RelationshipKind
    parent_role: ParentRole
