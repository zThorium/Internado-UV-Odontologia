from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date, datetime
from typing import Literal, Optional


WellbeingStatus = Literal["good", "regular", "difficult"]


class LogbookProcedureCreate(BaseModel):
    name: str  # no vacío
    description: str = ""
    quantity: int = Field(ge=1)  # >= 1


class LogbookProcedureOut(BaseModel):
    id: UUID
    name: str
    description: str
    quantity: int
    model_config = ConfigDict(from_attributes=True)


class LogbookEntryCreate(BaseModel):
    week_number: int = Field(ge=1)
    week_start_date: date
    wellbeing_status: WellbeingStatus  # obligatorio al crear
    procedures: list[LogbookProcedureCreate] = Field(min_length=1)
    # cohort_id es opcional — el backend lo resuelve desde el assignment activo
    cohort_id: Optional[UUID] = None


class LogbookEntryOut(BaseModel):
    id: UUID
    student_id: UUID
    cohort_id: UUID
    week_number: int
    week_start_date: date
    status: Literal["draft", "submitted", "reviewed"]
    wellbeing_status: Optional[WellbeingStatus]
    created_at: datetime
    updated_at: datetime
    procedures: list[LogbookProcedureOut]
    model_config = ConfigDict(from_attributes=True)


class LogbookEntryUpdate(BaseModel):
    week_number: Optional[int] = Field(None, ge=1)
    week_start_date: Optional[date] = None
    wellbeing_status: Optional[WellbeingStatus] = None
    procedures: list[LogbookProcedureCreate] = Field(min_length=1)


class LogbookStatusUpdate(BaseModel):
    status: Literal["reviewed"]  # coordinador solo puede marcar como reviewed
