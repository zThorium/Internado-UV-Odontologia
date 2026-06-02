"""
Servicio de alertas inteligentes para el coordinador.

Reglas de detección:
  no_bitacora:
    AMARILLO — sin bitácora 2 semanas consecutivas
    ROJO     — sin bitácora 3+ semanas

  low_wellbeing:
    AMARILLO — 2 semanas consecutivas con "regular" o "difícil"
    ROJO     — "difícil" 2 semanas consecutivas, o 3 veces en las últimas 5

  no_evaluation:
    AMARILLO — tutor no evaluó al estudiante en 3 semanas
    ROJO     — tutor no evaluó al estudiante en 5+ semanas

    no_tutor_validation:
        AMARILLO — bitácora sin validación de tutor por 2 semanas
        ROJO     — bitácora sin validación de tutor por 4+ semanas

  absences:
    AMARILLO — más de 2 ausencias injustificadas en el mes actual
    ROJO     — más de 4 ausencias injustificadas en el mes actual

  incident_report:
    ROJO INMEDIATO — el estudiante envió un incidente (cualquier estado)
"""
import uuid
from uuid import UUID
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord
from app.models.evaluation import Evaluation
from app.models.incident import Incident
from app.models.logbook import LogbookEntry
from app.models.logbook_validation import LogbookValidation
from app.models.student_alert import StudentAlert
from app.models.user import User
from app.schemas.alerts import (
    AlertSummary,
    ResolveAlertRequest,
    StudentAlertDetail,
    StudentAlertOut,
    StudentTrafficLight,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _weeks_since(ref_date: date) -> int:
    return (date.today() - ref_date).days // 7


def _month_start() -> date:
    today = date.today()
    return today.replace(day=1)


# ── Evaluación de reglas por estudiante ──────────────────────────────────────

async def _check_no_bitacora(
    student_id: UUID, assignment: Assignment, db: AsyncSession
) -> str | None:
    """Retorna 'red', 'yellow' o None."""
    # Última entrada de bitácora del estudiante
    result = await db.execute(
        select(LogbookEntry.week_start_date)
        .where(LogbookEntry.student_id == student_id)
        .order_by(LogbookEntry.week_start_date.desc())
        .limit(1)
    )
    last_entry_date = result.scalar_one_or_none()

    if last_entry_date is None:
        # Nunca registró — contar desde el inicio del assignment
        weeks_missing = _weeks_since(assignment.start_date)
    else:
        weeks_missing = _weeks_since(last_entry_date)

    if weeks_missing >= 3:
        return "red"
    if weeks_missing >= 2:
        return "yellow"
    return None


async def _check_low_wellbeing(student_id: UUID, db: AsyncSession) -> str | None:
    result = await db.execute(
        select(LogbookEntry.wellbeing_status)
        .where(
            LogbookEntry.student_id == student_id,
            LogbookEntry.wellbeing_status.isnot(None),
        )
        .order_by(LogbookEntry.week_number.desc())
        .limit(5)
    )
    statuses = [row[0] for row in result.fetchall()]

    if len(statuses) < 2:
        return None

    last2 = statuses[:2]
    last5 = statuses[:5]

    if last2 == ["difficult", "difficult"]:
        return "red"
    if last5.count("difficult") >= 3:
        return "red"
    if all(s in ("regular", "difficult") for s in last2):
        return "yellow"
    return None


async def _check_no_evaluation(
    student_id: UUID, assignment: Assignment, db: AsyncSession
) -> str | None:
    result = await db.execute(
        select(Evaluation.created_at)
        .where(Evaluation.student_id == student_id)
        .order_by(Evaluation.created_at.desc())
        .limit(1)
    )
    last_eval = result.scalar_one_or_none()

    if last_eval is None:
        weeks_since = _weeks_since(assignment.start_date)
    else:
        weeks_since = _weeks_since(last_eval.date())

    if weeks_since >= 5:
        return "red"
    if weeks_since >= 3:
        return "yellow"
    return None


async def _check_no_tutor_validation(student_id: UUID, db: AsyncSession) -> str | None:
    threshold_weeks = max(1, settings.TUTOR_LOGBOOK_VALIDATION_ALERT_WEEKS)
    result = await db.execute(
        select(LogbookEntry.week_start_date)
        .outerjoin(LogbookValidation, LogbookValidation.entry_id == LogbookEntry.id)
        .where(
            LogbookEntry.student_id == student_id,
            LogbookValidation.id.is_(None),
        )
        .order_by(LogbookEntry.week_start_date.asc())
    )
    unvalidated_dates = [row[0] for row in result.fetchall()]
    if not unvalidated_dates:
        return None

    oldest_unvalidated = unvalidated_dates[0]
    overdue_weeks = _weeks_since(oldest_unvalidated)

    if overdue_weeks >= threshold_weeks + 2:
        return "red"
    if overdue_weeks >= threshold_weeks:
        return "yellow"
    return None


async def _check_absences(student_id: UUID, db: AsyncSession) -> str | None:
    month_start = _month_start()
    result = await db.execute(
        select(func.count())
        .select_from(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == "absent",
            AttendanceRecord.date >= month_start,
        )
    )
    count = result.scalar_one() or 0

    if count > 4:
        return "red"
    if count > 2:
        return "yellow"
    return None


async def _check_incident_report(student_id: UUID, db: AsyncSession) -> str | None:
    result = await db.execute(
        select(func.count())
        .select_from(Incident)
        .where(Incident.student_id == student_id)
    )
    count = result.scalar_one() or 0
    return "red" if count > 0 else None


# ── Descripciones en lenguaje humano ─────────────────────────────────────────

_DESCRIPTIONS = {
    ("no_bitacora", "yellow"): "Sin registrar bitácora por 2 semanas consecutivas",
    ("no_bitacora", "red"):    "Sin registrar bitácora por 3 semanas o más",
    ("low_wellbeing", "yellow"): "Ha reportado bienestar bajo 2 semanas seguidas",
    ("low_wellbeing", "red"):    "Ha reportado una semana difícil 2 veces seguidas, o 3 veces en las últimas 5 semanas",
    ("no_evaluation", "yellow"): "El tutor no ha enviado una evaluación en 3 semanas",
    ("no_evaluation", "red"):    "El tutor no ha enviado una evaluación en 5 semanas o más",
    ("no_tutor_validation", "yellow"): "La bitácora no fue validada por tutor en el periodo esperado",
    ("no_tutor_validation", "red"): "La bitácora acumula más de 4 semanas sin validación de tutor",
    ("absences", "yellow"): "Más de 2 ausencias injustificadas este mes",
    ("absences", "red"):    "Más de 4 ausencias injustificadas este mes",
    ("incident_report", "red"): "El estudiante ha enviado un reporte de incidente",
}

_TYPE_LABELS = {
    "no_bitacora":    "Bitácora",
    "low_wellbeing":  "Bienestar",
    "no_evaluation":  "Evaluación",
    "no_tutor_validation": "Validación de tutor",
    "absences":       "Asistencia",
    "incident_report": "Incidente",
}


def _describe(alert_type: str, alert_level: str) -> str:
    return _DESCRIPTIONS.get((alert_type, alert_level), f"{alert_type} — {alert_level}")


# ── Job principal: evaluar todos los estudiantes ──────────────────────────────

async def run_alert_evaluation(db: AsyncSession) -> dict:
    """
    Evalúa todos los estudiantes activos contra todas las reglas.
    - Crea alertas nuevas si se cumple la condición y no existe una activa del mismo tipo
    - Resuelve automáticamente alertas que ya no apliquen
    Retorna un resumen de lo que se creó/resolvió.
    """
    students_result = await db.execute(
        select(User).where(User.role == "student", User.is_active.is_(True))
    )
    students = students_result.scalars().all()

    created = 0
    auto_resolved = 0

    for student in students:
        # Obtener assignment activo
        assignment_result = await db.execute(
            select(Assignment).where(
                Assignment.student_id == student.id,
                Assignment.is_active.is_(True),
            ).limit(1)
        )
        assignment = assignment_result.scalar_one_or_none()
        if assignment is None:
            continue  # sin assignment activo, no evaluar

        # Evaluar cada regla
        checks: dict[str, str | None] = {
            "no_bitacora":    await _check_no_bitacora(student.id, assignment, db),
            "low_wellbeing":  await _check_low_wellbeing(student.id, db),
            "no_evaluation":  await _check_no_evaluation(student.id, assignment, db),
            "no_tutor_validation": await _check_no_tutor_validation(student.id, db),
            "absences":       await _check_absences(student.id, db),
            "incident_report": await _check_incident_report(student.id, db),
        }

        # Obtener alertas activas del estudiante
        active_result = await db.execute(
            select(StudentAlert).where(
                StudentAlert.student_id == student.id,
                StudentAlert.is_active.is_(True),
            )
        )
        active_alerts = {a.alert_type: a for a in active_result.scalars().all()}

        for alert_type, new_level in checks.items():
            existing = active_alerts.get(alert_type)

            if new_level is None:
                # Condición ya no aplica → resolver automáticamente si existe
                if existing:
                    existing.is_active = False
                    existing.resolved_at = datetime.now(timezone.utc)
                    auto_resolved += 1
            else:
                if existing is None:
                    # Crear nueva alerta
                    db.add(StudentAlert(
                        id=uuid.uuid4(),
                        student_id=student.id,
                        alert_type=alert_type,
                        alert_level=new_level,
                        triggered_at=datetime.now(timezone.utc),
                        is_active=True,
                    ))
                    created += 1
                elif existing.alert_level != new_level:
                    # Escalar/desescalar: actualizar nivel
                    existing.alert_level = new_level

    await db.commit()
    return {"created": created, "auto_resolved": auto_resolved, "students_evaluated": len(students)}


# ── Consultas para el coordinador ─────────────────────────────────────────────

def _traffic_light(alerts: list[StudentAlert]) -> str:
    """Retorna 'red', 'yellow' o 'green' según el peor nivel activo."""
    levels = {a.alert_level for a in alerts if a.is_active}
    if "red" in levels:
        return "red"
    if "yellow" in levels:
        return "yellow"
    return "green"


async def get_students_traffic_light(db: AsyncSession) -> list[StudentTrafficLight]:
    """Lista de todos los estudiantes con su semáforo y alertas activas."""
    students_result = await db.execute(
        select(User).where(User.role == "student", User.is_active.is_(True))
        .order_by(User.full_name.asc())
    )
    students = students_result.scalars().all()

    result = []
    for student in students:
        alerts_result = await db.execute(
            select(StudentAlert).where(
                StudentAlert.student_id == student.id,
                StudentAlert.is_active.is_(True),
            ).order_by(StudentAlert.triggered_at.desc())
        )
        active_alerts = alerts_result.scalars().all()
        light = _traffic_light(active_alerts)

        result.append(StudentTrafficLight(
            student_id=student.id,
            student_name=student.full_name,
            traffic_light=light,
            active_alerts=[
                StudentAlertOut(
                    id=a.id,
                    student_id=a.student_id,
                    alert_type=a.alert_type,
                    alert_type_label=_TYPE_LABELS.get(a.alert_type, a.alert_type),
                    alert_level=a.alert_level,
                    description=_describe(a.alert_type, a.alert_level),
                    triggered_at=a.triggered_at,
                    is_active=a.is_active,
                    resolved_at=a.resolved_at,
                    coordinator_note=a.coordinator_note,
                )
                for a in active_alerts
            ],
        ))

    # Ordenar: rojo primero, luego amarillo, luego verde
    order = {"red": 0, "yellow": 1, "green": 2}
    result.sort(key=lambda s: order[s.traffic_light])
    return result


async def get_alerts_summary(db: AsyncSession) -> AlertSummary:
    """Conteo global rojo/amarillo/verde para el widget del dashboard."""
    students = await get_students_traffic_light(db)
    red = sum(1 for s in students if s.traffic_light == "red")
    yellow = sum(1 for s in students if s.traffic_light == "yellow")
    green = sum(1 for s in students if s.traffic_light == "green")
    return AlertSummary(red=red, yellow=yellow, green=green)


async def get_student_alert_detail(
    student_id: UUID, db: AsyncSession
) -> StudentAlertDetail:
    """Detalle completo de alertas activas e historial resuelto de un estudiante."""
    student = await db.get(User, student_id)
    if student is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    active_result = await db.execute(
        select(StudentAlert).where(
            StudentAlert.student_id == student_id,
            StudentAlert.is_active.is_(True),
        ).order_by(StudentAlert.triggered_at.desc())
    )
    active = active_result.scalars().all()

    resolved_result = await db.execute(
        select(StudentAlert).where(
            StudentAlert.student_id == student_id,
            StudentAlert.is_active.is_(False),
        ).order_by(StudentAlert.resolved_at.desc()).limit(20)
    )
    resolved = resolved_result.scalars().all()

    def _to_out(a: StudentAlert) -> StudentAlertOut:
        return StudentAlertOut(
            id=a.id,
            student_id=a.student_id,
            alert_type=a.alert_type,
            alert_type_label=_TYPE_LABELS.get(a.alert_type, a.alert_type),
            alert_level=a.alert_level,
            description=_describe(a.alert_type, a.alert_level),
            triggered_at=a.triggered_at,
            is_active=a.is_active,
            resolved_at=a.resolved_at,
            coordinator_note=a.coordinator_note,
        )

    return StudentAlertDetail(
        student_id=student.id,
        student_name=student.full_name,
        traffic_light=_traffic_light(active),
        active_alerts=[_to_out(a) for a in active],
        resolved_alerts=[_to_out(a) for a in resolved],
    )


async def resolve_student_alert(
    alert_id: UUID,
    coordinator_id: UUID,
    note: str | None,
    db: AsyncSession,
) -> StudentAlertOut:
    alert = await db.get(StudentAlert, alert_id)
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    alert.is_active = False
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = coordinator_id
    alert.coordinator_note = note
    await db.commit()

    return StudentAlertOut(
        id=alert.id,
        student_id=alert.student_id,
        alert_type=alert.alert_type,
        alert_type_label=_TYPE_LABELS.get(alert.alert_type, alert.alert_type),
        alert_level=alert.alert_level,
        description=_describe(alert.alert_type, alert.alert_level),
        triggered_at=alert.triggered_at,
        is_active=alert.is_active,
        resolved_at=alert.resolved_at,
        coordinator_note=alert.coordinator_note,
    )
