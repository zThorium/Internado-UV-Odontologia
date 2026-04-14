from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional


AlertLevel = Literal["yellow", "red"]
TrafficLight = Literal["green", "yellow", "red"]
AlertType = Literal[
    "no_bitacora",
    "low_wellbeing",
    "no_evaluation",
    "no_tutor_validation",
    "absences",
    "incident_report",
]


class StudentAlertOut(BaseModel):
    id: UUID
    student_id: UUID
    alert_type: AlertType
    alert_type_label: str       # etiqueta legible: "Bitácora", "Bienestar", etc.
    alert_level: AlertLevel
    description: str            # descripción en lenguaje humano
    triggered_at: datetime
    is_active: bool
    resolved_at: Optional[datetime]
    coordinator_note: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class StudentTrafficLight(BaseModel):
    """Resumen de un estudiante con su semáforo y alertas activas."""
    student_id: UUID
    student_name: str
    traffic_light: TrafficLight
    active_alerts: list[StudentAlertOut]


class StudentAlertDetail(BaseModel):
    """Detalle completo de alertas de un estudiante."""
    student_id: UUID
    student_name: str
    traffic_light: TrafficLight
    active_alerts: list[StudentAlertOut]
    resolved_alerts: list[StudentAlertOut]


class AlertSummary(BaseModel):
    """Conteo global para el widget del dashboard."""
    red: int
    yellow: int
    green: int


class ResolveAlertRequest(BaseModel):
    coordinator_note: Optional[str] = None
