from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.db.session import get_db
from app.schemas.auth import UserInToken
from app.schemas.attendance import AttendanceCreate, AttendanceOut, AttendanceUpdate, AttendanceStats
from app.services.attendance import (
    create_attendance,
    update_attendance,
    get_attendance_for_student,
    get_attendance_stats,
)

router = APIRouter()


@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def register_attendance(
    data: AttendanceCreate,
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """Estudiante registra su propia asistencia diaria."""
    return await create_attendance(data, current_user, db)


@router.patch("/{record_id}", response_model=AttendanceOut)
async def edit_attendance(
    record_id: UUID,
    data: AttendanceUpdate,
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """Estudiante edita un registro de asistencia propio."""
    return await update_attendance(record_id, data, current_user, db)


@router.get("/me", response_model=list[AttendanceOut])
async def my_attendance(
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """Estudiante consulta su propio historial de asistencia."""
    return await get_attendance_for_student(UUID(current_user.id), current_user, db)


@router.get("/students/{student_id}", response_model=list[AttendanceOut])
async def student_attendance(
    student_id: UUID,
    current_user: UserInToken = Depends(require_role("coordinator", "tutor")),
    db: AsyncSession = Depends(get_db),
):
    """
    Coordinador: ve asistencia de cualquier estudiante.
    Tutor: solo ve asistencia de sus estudiantes asignados.
    """
    return await get_attendance_for_student(student_id, current_user, db)


@router.get("/students/{student_id}/stats", response_model=AttendanceStats)
async def student_attendance_stats(
    student_id: UUID,
    current_user: UserInToken = Depends(require_role("coordinator", "tutor")),
    db: AsyncSession = Depends(get_db),
):
    """Estadísticas de asistencia de un estudiante."""
    return await get_attendance_stats(student_id, current_user, db)
