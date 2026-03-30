from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.db.session import get_db
from app.schemas.alerts import (
    AlertSummary,
    ResolveAlertRequest,
    StudentAlertDetail,
    StudentAlertOut,
    StudentTrafficLight,
)
from app.schemas.auth import UserInToken
from app.services.alerts import (
    get_alerts_summary,
    get_student_alert_detail,
    get_students_traffic_light,
    resolve_student_alert,
    run_alert_evaluation,
)

router = APIRouter()
_coordinator = Depends(require_role("coordinator"))


@router.post("/run", summary="Ejecutar evaluación de alertas manualmente")
async def trigger_evaluation(
    _: UserInToken = _coordinator,
    db: AsyncSession = Depends(get_db),
):
    """
    Dispara el job de evaluación de alertas de forma manual.
    En producción esto lo correría un scheduler diario (cron/APScheduler).
    """
    result = await run_alert_evaluation(db)
    return result


@router.get("/summary", response_model=AlertSummary)
async def alerts_summary(
    _: UserInToken = _coordinator,
    db: AsyncSession = Depends(get_db),
):
    """Conteo global rojo/amarillo/verde para el widget del dashboard."""
    return await get_alerts_summary(db)


@router.get("/students", response_model=list[StudentTrafficLight])
async def students_traffic_light(
    _: UserInToken = _coordinator,
    db: AsyncSession = Depends(get_db),
):
    """Lista de todos los estudiantes con su semáforo y alertas activas, ordenados por severidad."""
    return await get_students_traffic_light(db)


@router.get("/students/{student_id}", response_model=StudentAlertDetail)
async def student_alert_detail(
    student_id: UUID,
    _: UserInToken = _coordinator,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de alertas activas e historial resuelto de un estudiante."""
    return await get_student_alert_detail(student_id, db)


@router.post("/resolve/{alert_id}", response_model=StudentAlertOut)
async def resolve_alert(
    alert_id: UUID,
    body: ResolveAlertRequest,
    current_user: UserInToken = _coordinator,
    db: AsyncSession = Depends(get_db),
):
    """Marcar una alerta como atendida con nota opcional del coordinador."""
    return await resolve_student_alert(
        alert_id, UUID(current_user.id), body.coordinator_note, db
    )
