import uuid
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.attendance import AttendanceRecord
from app.models.assignment import Assignment
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceStats
from app.schemas.auth import UserInToken


async def create_attendance(
    data: AttendanceCreate,
    current_user: UserInToken,
    db: AsyncSession,
) -> AttendanceRecord:
    """
    Solo el estudiante puede registrar su propia asistencia.
    No puede haber dos registros para el mismo estudiante y fecha.
    """
    student_id = uuid.UUID(current_user.id)

    existing = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.date == data.date,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un registro de asistencia para esta fecha",
        )

    record = AttendanceRecord(
        student_id=student_id,
        date=data.date,
        status=data.status,
        observation=data.observation,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def update_attendance(
    record_id: UUID,
    data: AttendanceUpdate,
    current_user: UserInToken,
    db: AsyncSession,
) -> AttendanceRecord:
    """
    El estudiante solo puede editar sus propios registros.
    """
    student_id = uuid.UUID(current_user.id)

    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    if record.student_id != student_id:
        raise HTTPException(status_code=403, detail="No puedes editar registros de otro estudiante")

    record.status = data.status
    record.observation = data.observation
    record.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    return record


async def get_attendance_for_student(
    student_id: UUID,
    current_user: UserInToken,
    db: AsyncSession,
) -> list[AttendanceRecord]:
    """
    Control de acceso:
    - student: solo puede ver su propia asistencia
    - coordinator: puede ver cualquier estudiante
    - tutor: solo puede ver estudiantes que tiene asignados (solo lectura)
    """
    if current_user.role == "student":
        if str(student_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Solo puedes ver tu propia asistencia")

    elif current_user.role == "tutor":
        # Verificar que el estudiante está asignado a este tutor
        tutor_id = uuid.UUID(current_user.id)
        result = await db.execute(
            select(Assignment).where(
                Assignment.tutor_id == tutor_id,
                Assignment.student_id == student_id,
                Assignment.is_active.is_(True),
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes ver la asistencia de tus estudiantes asignados",
            )

    result = await db.execute(
        select(AttendanceRecord)
        .where(AttendanceRecord.student_id == student_id)
        .order_by(AttendanceRecord.date.desc())
    )
    return list(result.scalars().all())


async def get_attendance_stats(
    student_id: UUID,
    current_user: UserInToken,
    db: AsyncSession,
) -> AttendanceStats:
    """
    Calcula estadísticas de asistencia para un estudiante.
    Mismas reglas de acceso que get_attendance_for_student.
    """
    records = await get_attendance_for_student(student_id, current_user, db)

    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    justified = sum(1 for r in records if r.status == "justified")
    rate = round((present / total * 100), 1) if total > 0 else 0.0

    return AttendanceStats(
        total=total,
        present=present,
        absent=absent,
        justified=justified,
        attendance_rate=rate,
    )
