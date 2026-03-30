"""
Servicio de bienestar estudiantil.

Reglas de alerta:
- AMARILLA: "regular" o "difficult" 2 semanas consecutivas
- ROJA:     "difficult" 2 semanas consecutivas
            O "difficult" 3 veces en las últimas 5 semanas

Las alertas son idempotentes: si ya existe una alerta activa del mismo nivel
para el estudiante, no se crea una nueva.
"""
import uuid
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.logbook import LogbookEntry
from app.models.wellbeing import WellbeingAlert
from app.models.user import User
from app.schemas.wellbeing import (
    StudentWellbeingSummary,
    WellbeingAlertOut,
    WellbeingDashboardSummary,
    WellbeingHistoryItem,
)


# ── Lógica de evaluación de alertas ──────────────────────────────────────────

def _evaluate_alert(recent: list[str]) -> str | None:
    """
    Recibe lista de wellbeing_status ordenada de más reciente a más antigua.
    Retorna 'red', 'yellow' o None.
    """
    if len(recent) < 2:
        return None

    last2 = recent[:2]
    last5 = recent[:5]

    # ROJA: 2 "difficult" consecutivos
    if last2 == ["difficult", "difficult"]:
        return "red"

    # ROJA: 3 "difficult" en las últimas 5 semanas
    if last5.count("difficult") >= 3:
        return "red"

    # AMARILLA: 2 semanas consecutivas con "regular" o "difficult"
    if all(s in ("regular", "difficult") for s in last2):
        return "yellow"

    return None


# ── Función principal: evaluar y crear alerta si corresponde ─────────────────

async def evaluate_and_create_alert(
    student_id: UUID,
    db: AsyncSession,
) -> WellbeingAlert | None:
    """
    Llamar después de guardar una nueva entrada de bitácora con wellbeing_status.
    Evalúa el historial reciente y crea una alerta si corresponde.
    """
    # Obtener las últimas 5 entradas con wellbeing_status, ordenadas desc
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

    new_level = _evaluate_alert(statuses)
    if new_level is None:
        return None

    # Idempotencia: no crear si ya existe alerta activa del mismo nivel
    existing = await db.execute(
        select(WellbeingAlert).where(
            WellbeingAlert.student_id == student_id,
            WellbeingAlert.resolved.is_(False),
            WellbeingAlert.alert_level == new_level,
        )
    )
    if existing.scalar_one_or_none():
        return None

    alert = WellbeingAlert(
        id=uuid.uuid4(),
        student_id=student_id,
        alert_level=new_level,
        triggered_at=datetime.now(timezone.utc),
        resolved=False,
    )
    db.add(alert)
    await db.commit()
    return alert


# ── Historial de bienestar del estudiante (últimas 8 semanas) ────────────────

async def get_student_wellbeing_history(
    student_id: UUID,
    db: AsyncSession,
    limit: int = 8,
) -> list[WellbeingHistoryItem]:
    result = await db.execute(
        select(LogbookEntry)
        .where(
            LogbookEntry.student_id == student_id,
            LogbookEntry.wellbeing_status.isnot(None),
        )
        .order_by(LogbookEntry.week_number.desc())
        .limit(limit)
    )
    entries = result.scalars().all()
    return [
        WellbeingHistoryItem(
            week_number=e.week_number,
            week_start_date=str(e.week_start_date),
            wellbeing_status=e.wellbeing_status,
        )
        for e in reversed(entries)  # cronológico asc para la vista
    ]


# ── Alerta activa de un estudiante ───────────────────────────────────────────

async def get_active_alert(
    student_id: UUID,
    db: AsyncSession,
) -> WellbeingAlert | None:
    result = await db.execute(
        select(WellbeingAlert)
        .where(
            WellbeingAlert.student_id == student_id,
            WellbeingAlert.resolved.is_(False),
        )
        .order_by(WellbeingAlert.triggered_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ── Resumen para el coordinador ───────────────────────────────────────────────

async def get_coordinator_wellbeing_summary(
    db: AsyncSession,
) -> tuple[list[StudentWellbeingSummary], WellbeingDashboardSummary]:
    """
    Retorna lista de resúmenes por estudiante + conteo global verde/amarillo/rojo.
    """
    # Todos los estudiantes activos
    students_result = await db.execute(
        select(User).where(User.role == "student", User.is_active.is_(True))
    )
    students = students_result.scalars().all()

    summaries: list[StudentWellbeingSummary] = []
    counts = {"green": 0, "yellow": 0, "red": 0}

    for student in students:
        history = await get_student_wellbeing_history(student.id, db)
        alert = await get_active_alert(student.id, db)
        level = alert.alert_level if alert else None

        if level == "red":
            counts["red"] += 1
        elif level == "yellow":
            counts["yellow"] += 1
        else:
            counts["green"] += 1

        summaries.append(StudentWellbeingSummary(
            student_id=student.id,
            student_name=student.full_name,
            alert_level=level,
            history=history,
        ))

    dashboard = WellbeingDashboardSummary(**counts)
    return summaries, dashboard


# ── Resolver alerta (coordinador) ─────────────────────────────────────────────

async def resolve_alert(
    alert_id: UUID,
    db: AsyncSession,
) -> WellbeingAlert | None:
    result = await db.execute(
        select(WellbeingAlert).where(WellbeingAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if alert and not alert.resolved:
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        await db.commit()
    return alert
