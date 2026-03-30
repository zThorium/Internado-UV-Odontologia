from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional


WellbeingStatus = Literal["good", "regular", "difficult"]
AlertLevel = Literal["yellow", "red"]


class WellbeingHistoryItem(BaseModel):
    """Un punto en el historial de bienestar del estudiante."""
    week_number: int
    week_start_date: str
    wellbeing_status: WellbeingStatus
    model_config = ConfigDict(from_attributes=True)


class WellbeingAlertOut(BaseModel):
    id: UUID
    student_id: UUID
    alert_level: AlertLevel
    triggered_at: datetime
    resolved: bool
    resolved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class StudentWellbeingSummary(BaseModel):
    """Resumen de bienestar de un estudiante para el coordinador."""
    student_id: UUID
    student_name: str
    alert_level: Optional[AlertLevel]   # None = verde (sin alerta activa)
    history: list[WellbeingHistoryItem]  # últimas 8 semanas


class WellbeingDashboardSummary(BaseModel):
    """Resumen global para el panel del coordinador."""
    green: int
    yellow: int
    red: int
