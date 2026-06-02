from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Literal


class EvaluationItemCreate(BaseModel):
    dimension: str
    score: int = Field(ge=1, le=5)
    comment: str | None = None


class EvaluationItemOut(BaseModel):
    id: UUID
    evaluation_id: UUID
    dimension: str
    score: int
    comment: str | None
    model_config = ConfigDict(from_attributes=True)


class EvaluationCreate(BaseModel):
    student_id: UUID
    assignment_id: UUID
    period_label: str
    overall_comment: str | None = None
    items: list[EvaluationItemCreate] = Field(min_length=1)


class EvaluationOut(BaseModel):
    id: UUID
    tutor_id: UUID
    student_id: UUID
    assignment_id: UUID
    period_label: str
    student_name: str | None = None
    tutor_name: str | None = None
    clinical_site: str | None = None
    average_score: float | None = None
    overall_comment: str | None
    created_at: datetime
    items: list[EvaluationItemOut]
    model_config = ConfigDict(from_attributes=True)


class StudentSummary(BaseModel):
    id: UUID
    full_name: str
    email: str
    tutor_name: str | None = None
    clinical_site: str
    assignment_id: UUID
    model_config = ConfigDict(from_attributes=True)
