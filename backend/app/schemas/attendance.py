from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Literal


AttendanceStatus = Literal["present", "absent", "justified"]


class AttendanceCreate(BaseModel):
    date: date
    status: AttendanceStatus
    observation: str | None = None


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus
    observation: str | None = None


class AttendanceOut(BaseModel):
    id: UUID
    student_id: UUID
    date: date
    status: AttendanceStatus
    observation: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AttendanceStats(BaseModel):
    total: int
    present: int
    absent: int
    justified: int
    attendance_rate: float  # porcentaje de días presentes sobre total
