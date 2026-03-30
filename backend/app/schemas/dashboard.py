from datetime import date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


CareLevel = Literal["primary", "secondary", "tertiary"]


class DashboardStats(BaseModel):
    total_students: int
    total_tutors: int
    total_entries: int
    pending_entries: int
    total_incidents: int
    open_incidents: int


class AssignmentCreate(BaseModel):
    student_id: UUID
    tutor_id: UUID
    cohort_id: UUID
    care_level: CareLevel = "primary"
    clinical_site: str
    start_date: date
    end_date: date


class AssignmentOut(BaseModel):
    id: UUID
    student_id: UUID
    tutor_id: UUID
    cohort_id: UUID
    care_level: CareLevel
    clinical_site: str
    start_date: date
    end_date: date
    is_active: bool
    # Nombres resueltos (opcionales — se rellenan en el servicio)
    student_name: str | None = None
    tutor_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CohortOut(BaseModel):
    id: UUID
    name: str
    year: int
    semester: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class CohortCreate(BaseModel):
    year: int = Field(ge=2020, le=2100)
    semester: int = Field(ge=1, le=2)
    name: str | None = None
    is_active: bool = True


class CohortUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class TutorCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class TutorOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class DashboardTrends(BaseModel):
    total_students: int
    total_tutors: int
    total_entries: int
    pending_entries: int
    total_incidents: int
    open_incidents: int


ActivityKind = Literal[
    "logbook_created",
    "evaluation_created",
    "incident_created",
    "incident_status_changed",
]


class ActivityItem(BaseModel):
    id: str
    kind: ActivityKind
    level: Literal["normal", "critical"]
    student_id: UUID
    student_name: str
    description: str
    occurred_at: datetime


class RecentActivityResponse(BaseModel):
    items: list[ActivityItem]


class WellbeingQuickItem(BaseModel):
    student_id: UUID
    student_name: str
    alert_level: Literal["yellow", "red"]
    alert_type: str
    triggered_at: datetime


class WellbeingQuickResponse(BaseModel):
    total_active: int
    items: list[WellbeingQuickItem]


MetricSeriesKey = Literal[
    "total_students",
    "total_entries",
    "open_incidents",
    "pending_entries",
]


class MetricSeriesPoint(BaseModel):
    label: str
    value: int


class MetricSeries(BaseModel):
    key: MetricSeriesKey
    points: list[MetricSeriesPoint]


class DashboardMetricSeriesResponse(BaseModel):
    series: list[MetricSeries]
