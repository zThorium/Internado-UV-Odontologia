import uuid
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.logbook import LogbookEntry, LogbookProcedure
from app.models.assignment import Assignment
from app.schemas.logbook import LogbookEntryCreate, LogbookEntryUpdate, LogbookStatusUpdate
from app.schemas.auth import UserInToken
from app.services.wellbeing import evaluate_and_create_alert


async def _resolve_cohort_id(student_id: UUID, provided: UUID | None, db: AsyncSession) -> UUID:
    """
    Si el cliente provee cohort_id, lo usa directamente.
    Si no, busca el assignment activo del estudiante y usa su cohort_id.
    Lanza 422 si no hay assignment activo.
    """
    if provided is not None:
        return provided

    result = await db.execute(
        select(Assignment).where(
            Assignment.student_id == student_id,
            Assignment.is_active.is_(True),
        ).limit(1)
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(
            status_code=422,
            detail="No tienes una asignación activa. Contacta al coordinador.",
        )
    return assignment.cohort_id


async def create_logbook_entry(
    entry: LogbookEntryCreate,
    current_user: UserInToken,
    db: AsyncSession,
) -> LogbookEntry:
    """
    Precondiciones (del diseño):
    - current_user.role == "student"
    - entry.week_number >= 1
    - entry.procedures es lista no vacía
    - No existe entrada para (student_id, week_number, cohort_id) con status != "draft"

    Postcondiciones:
    - Se crea LogbookEntry con status="draft"
    - Se crean N LogbookProcedure asociados
    - entry.student_id == current_user.id
    - Retorna la entrada creada con sus procedimientos

    Si ya existe entrada para esa semana/cohorte → lanza HTTPException(409)
    """
    student_id = uuid.UUID(current_user.id)

    # Resolver cohort_id desde assignment activo si no se proveyó
    cohort_id = await _resolve_cohort_id(student_id, entry.cohort_id, db)

    # 1. Verificar unicidad: no debe existir entrada para (student_id, week_number, cohort_id)
    result = await db.execute(
        select(LogbookEntry).where(
            LogbookEntry.student_id == student_id,
            LogbookEntry.week_number == entry.week_number,
            LogbookEntry.cohort_id == cohort_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una entrada para esta semana en esta cohorte",
        )

    # 2. Crear LogbookEntry con status="draft"
    entry_obj = LogbookEntry(
        student_id=student_id,
        cohort_id=cohort_id,
        week_number=entry.week_number,
        week_start_date=entry.week_start_date,
        status="draft",
        wellbeing_status=entry.wellbeing_status,
    )
    db.add(entry_obj)
    await db.flush()  # obtener entry_obj.id antes de crear procedimientos

    # 3. Crear LogbookProcedure para cada procedimiento
    for proc in entry.procedures:
        procedure = LogbookProcedure(
            entry_id=entry_obj.id,
            name=proc.name,
            description=proc.description,
            quantity=proc.quantity,
        )
        db.add(procedure)

    await db.commit()

    # 4. Evaluar alertas de bienestar (no bloquea si falla)
    try:
        await evaluate_and_create_alert(student_id, db)
    except Exception:
        pass
    
    # 5. Ejecutar evaluación completa de alertas para este estudiante
    try:
        from app.services.alerts import run_alert_evaluation
        await run_alert_evaluation(db)
    except Exception:
        pass

    # Recargar con procedimientos usando selectinload para evitar lazy-loading
    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.id == entry_obj.id)
    )
    return result.scalar_one()


async def update_logbook_entry(
    entry_id: UUID,
    updates: LogbookEntryUpdate,
    current_user: UserInToken,
    db: AsyncSession,
) -> LogbookEntry:
    """
    Precondiciones:
    - current_user.role == "student"
    - entry_id corresponde a una entrada existente
    - entry.student_id == current_user.id
    - entry.status == "draft"

    Postcondiciones:
    - Los procedimientos anteriores son eliminados y reemplazados por los nuevos
    - week_number, week_start_date y wellbeing_status se actualizan si se proveen
    - entry.updated_at se actualiza
    - Retorna la entrada actualizada con sus procedimientos
    """
    student_id = uuid.UUID(current_user.id)

    # 1. Obtener la entrada con procedimientos cargados
    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    # 2. Verificar existencia
    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    # 3. Verificar propiedad
    if entry.student_id != student_id:
        raise HTTPException(status_code=403, detail="No puedes editar entradas de otro estudiante")

    # 4. Verificar estado draft
    if entry.status != "draft":
        raise HTTPException(status_code=409, detail="Solo se pueden editar entradas en estado borrador")

    # 5. Actualizar campos opcionales si se proveen
    if updates.week_number is not None:
        entry.week_number = updates.week_number
    if updates.week_start_date is not None:
        entry.week_start_date = updates.week_start_date
    if updates.wellbeing_status is not None:
        entry.wellbeing_status = updates.wellbeing_status

    # 6. Reemplazar procedimientos: eliminar existentes e insertar nuevos
    for proc in list(entry.procedures):
        await db.delete(proc)
    await db.flush()

    for proc_data in updates.procedures:
        new_proc = LogbookProcedure(
            entry_id=entry.id,
            name=proc_data.name,
            description=proc_data.description,
            quantity=proc_data.quantity,
        )
        db.add(new_proc)

    # 7. Actualizar updated_at
    entry.updated_at = datetime.now(timezone.utc)

    # 8. Commit y retornar con procedimientos cargados
    await db.commit()
    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.id == entry.id)
        .execution_options(populate_existing=True)
    )
    
    # 9. Evaluar alertas de bienestar si se actualizó el estado (no bloquea si falla)
    if updates.wellbeing_status is not None:
        try:
            await evaluate_and_create_alert(student_id, db)
        except Exception:
            pass
    
    # 10. Ejecutar evaluación completa de alertas para este estudiante
    try:
        from app.services.alerts import run_alert_evaluation
        await run_alert_evaluation(db)
    except Exception:
        pass
    
    return result.scalar_one()


async def get_logbook_entries(
    student_id: UUID,
    current_user: UserInToken,
    db: AsyncSession,
) -> list[LogbookEntry]:
    """
    Control de acceso del diseño:
    - Si role == "student": student_id DEBE ser == current_user.id → 403 si no
    - Si role == "coordinator": puede ver cualquier student_id
    - Si role == "tutor": NUNCA llega aquí (bloqueado en router con 403)

    Postcondiciones:
    - Resultado ordenado por week_number ASC
    """
    if current_user.role == "student" and str(student_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes ver tu propia bitácora")

    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.student_id == student_id)
        .order_by(LogbookEntry.week_number.asc())
    )
    return list(result.scalars().all())


async def get_logbook_entry_by_id(
    entry_id: UUID,
    current_user: UserInToken,
    db: AsyncSession,
) -> LogbookEntry:
    """
    - Si entry no existe → 404
    - Si role == "student" y entry.student_id != current_user.id → 403
    - Si role == "coordinator" → puede ver cualquier entrada
    """
    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    if current_user.role == "student" and str(entry.student_id) != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes ver entradas de otro estudiante")

    return entry


async def update_logbook_entry_status(
    entry_id: UUID,
    status_update: LogbookStatusUpdate,
    current_user: UserInToken,
    db: AsyncSession,
) -> LogbookEntry:
    """
    Solo coordinador puede cambiar status.
    - Si entry no existe → 404
    - Actualiza entry.status = status_update.status
    - Retorna entry actualizada
    """
    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    entry.status = status_update.status
    await db.commit()

    result = await db.execute(
        select(LogbookEntry)
        .options(selectinload(LogbookEntry.procedures))
        .where(LogbookEntry.id == entry_id)
    )
    return result.scalar_one()
