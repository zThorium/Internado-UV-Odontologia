from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Literal


class IncidentCreate(BaseModel):
    incident_type: Literal["abuse", "harassment", "discrimination", "other"]
    description: str
    event_date: date


class IncidentOut(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str | None = None
    student_email: str | None = None
    incident_type: str
    description: str
    event_date: date
    status: str
    coordinator_response: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class IncidentStatusUpdate(BaseModel):
    status: Literal["under_review", "resolved"]


class IncidentResponseUpdate(BaseModel):
    coordinator_response: str
