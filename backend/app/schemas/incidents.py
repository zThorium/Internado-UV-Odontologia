from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Literal


IncidentType = Literal["abuse", "harassment", "discrimination", "other"]
IncidentUrgency = Literal["low", "medium", "high", "critical"]
IncidentReporterRole = Literal["student", "tutor"]


class IncidentCreate(BaseModel):
    incident_type: IncidentType
    description: str
    event_date: date


class TutorIncidentCreate(BaseModel):
    student_id: UUID
    title: str
    description: str
    event_date: date
    urgency_level: IncidentUrgency = "medium"


class IncidentOut(BaseModel):
    id: UUID
    student_id: UUID
    reported_by_user_id: UUID | None = None
    reporter_role: IncidentReporterRole = "student"
    title: str | None = None
    student_name: str | None = None
    student_email: str | None = None
    reporter_name: str | None = None
    incident_type: str
    urgency_level: IncidentUrgency = "medium"
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
