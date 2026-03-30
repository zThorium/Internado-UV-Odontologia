from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import require_role
from app.db.session import get_db
from app.models.assignment import Assignment
from app.schemas.auth import UserInToken
from app.schemas.logbook import (
    LogbookEntryCreate,
    LogbookEntryOut,
    LogbookEntryUpdate,
    LogbookStatusUpdate,
)
from app.schemas.wellbeing import (
    StudentWellbeingSummary,
    WellbeingAlertOut,
    WellbeingDashboardSummary,
    WellbeingHistoryItem,
)
from app.services.logbook import (
    create_logbook_entry,
    get_logbook_entries,
    get_logbook_entry_by_id,
    update_logbook_entry,
    update_logbook_entry_status,
)
from app.services.wellbeing import (
    get_coordinator_wellbeing_summary,
    get_student_wellbeing_history,
    resolve_alert,
)
from app.services.procedure_catalog import get_procedure_catalog, normalize_care_level

router = APIRouter()

_student_or_coordinator = Depends(require_role("student", "coordinator"))
_coordinator_only = Depends(require_role("coordinator"))


@router.get("/my-context")
async def my_logbook_context(
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el contexto necesario para crear una entrada de bitácora:
    - cohort_id del assignment activo
    - week_number sugerido (semanas desde start_date del assignment)
    - week_start_date sugerida (lunes de la semana actual)
    """
    result = await db.execute(
        select(Assignment).where(
            Assignment.student_id == UUID(current_user.id),
            Assignment.is_active.is_(True),
        ).limit(1)
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=422, detail="No tienes una asignación activa.")

    today = date.today()
    # Lunes de la semana actual
    week_start = today - __import__('datetime').timedelta(days=today.weekday())
    # Semana relativa al inicio del assignment
    delta = (week_start - assignment.start_date).days
    week_number = max(1, delta // 7 + 1)

    return {
        "cohort_id": str(assignment.cohort_id),
        "week_number": week_number,
        "week_start_date": str(week_start),
        "care_level": normalize_care_level(assignment.care_level),
        "clinical_site": assignment.clinical_site,
        "allowed_procedures": get_procedure_catalog(assignment.care_level),
    }


@router.get("/entries", response_model=list[LogbookEntryOut])
async def list_my_entries(
    current_user: UserInToken = _student_or_coordinator,
    db: AsyncSession = Depends(get_db),
):
    return await get_logbook_entries(UUID(current_user.id), current_user, db)


@router.post("/entries", response_model=LogbookEntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry: LogbookEntryCreate,
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    return await create_logbook_entry(entry, current_user, db)


@router.get("/entries/{entry_id}", response_model=LogbookEntryOut)
async def get_entry(
    entry_id: UUID,
    current_user: UserInToken = _student_or_coordinator,
    db: AsyncSession = Depends(get_db),
):
    return await get_logbook_entry_by_id(entry_id, current_user, db)


@router.put("/entries/{entry_id}", response_model=LogbookEntryOut)
async def update_entry(
    entry_id: UUID,
    updates: LogbookEntryUpdate,
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    return await update_logbook_entry(entry_id, updates, current_user, db)


@router.patch("/entries/{entry_id}/status", response_model=LogbookEntryOut)
async def change_entry_status(
    entry_id: UUID,
    status_update: LogbookStatusUpdate,
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    return await update_logbook_entry_status(entry_id, status_update, current_user, db)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID,
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar una entrada de bitácora (solo si está en estado draft)."""
    from app.models.logbook import LogbookEntry
    
    result = await db.execute(
        select(LogbookEntry).where(LogbookEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    if str(entry.student_id) != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta entrada")
    
    if entry.status != "draft":
        raise HTTPException(
            status_code=422, 
            detail="Solo se pueden eliminar entradas en estado borrador"
        )
    
    await db.delete(entry)
    await db.commit()
    return None


@router.get("/students/{student_id}/entries", response_model=list[LogbookEntryOut])
async def list_student_entries(
    student_id: UUID,
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    return await get_logbook_entries(student_id, current_user, db)


# ── Wellbeing endpoints ───────────────────────────────────────────────────────

@router.get("/wellbeing/history", response_model=list[WellbeingHistoryItem])
async def my_wellbeing_history(
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """Historial de bienestar del estudiante autenticado (últimas 8 semanas)."""
    return await get_student_wellbeing_history(UUID(current_user.id), db)


@router.get("/wellbeing/coordinator-summary", response_model=WellbeingDashboardSummary)
async def coordinator_wellbeing_dashboard(
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    """Conteo global verde/amarillo/rojo para el panel del coordinador."""
    _, summary = await get_coordinator_wellbeing_summary(db)
    return summary


@router.get("/wellbeing/students", response_model=list[StudentWellbeingSummary])
async def coordinator_students_wellbeing(
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    """Lista de estudiantes con su nivel de alerta e historial."""
    summaries, _ = await get_coordinator_wellbeing_summary(db)
    return summaries


@router.get("/wellbeing/students/{student_id}/history", response_model=list[WellbeingHistoryItem])
async def student_wellbeing_history_for_coordinator(
    student_id: UUID,
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    """Historial de bienestar de un estudiante específico (solo coordinador)."""
    return await get_student_wellbeing_history(student_id, db)


@router.post("/wellbeing/alerts/{alert_id}/resolve", response_model=WellbeingAlertOut)
async def resolve_wellbeing_alert(
    alert_id: UUID,
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    """Marcar una alerta como resuelta."""
    from fastapi import HTTPException
    alert = await resolve_alert(alert_id, db)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert
