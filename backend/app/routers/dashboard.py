from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.db.session import get_db
from app.schemas.auth import UserInToken
from app.schemas.dashboard import (
    ActivityItem,
    AssignmentCreate,
    AssignmentOut,
    CohortCreate,
    CohortOut,
    CohortUpdate,
    DashboardMetricSeriesResponse,
    DashboardStats,
    DashboardTrends,
    RecentActivityResponse,
    TutorCreate,
    TutorOut,
    WellbeingQuickResponse,
)
from app.services.dashboard import (
    create_cohort,
    create_assignment,
    create_tutor,
    deactivate_assignment,
    get_dashboard_overview,
    get_dashboard_metric_series,
    get_dashboard_trends,
    get_recent_activity,
    get_wellbeing_quick,
    list_cohorts,
    list_assignments,
    list_tutors,
    update_cohort,
    update_tutor,
)

router = APIRouter()


class TutorUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


@router.get("/overview", response_model=DashboardStats)
async def dashboard_overview(
    cohort_id: UUID | None = None,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_overview(cohort_id, db)


@router.get("/overview-trends", response_model=DashboardTrends)
async def dashboard_overview_trends(
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_trends(db)


@router.get("/recent-activity", response_model=RecentActivityResponse)
async def dashboard_recent_activity(
    limit: int = 5,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    items: list[ActivityItem] = await get_recent_activity(db, limit=limit)
    return {"items": items}


@router.get("/wellbeing-quick", response_model=WellbeingQuickResponse)
async def dashboard_wellbeing_quick(
    limit: int = 3,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_wellbeing_quick(db, limit=limit)


@router.get("/metric-series", response_model=DashboardMetricSeriesResponse)
async def dashboard_metric_series(
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_metric_series(db)


@router.post(
    "/assignments",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment_endpoint(
    data: AssignmentCreate,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await create_assignment(data, db)


@router.get("/assignments", response_model=list[AssignmentOut])
async def list_assignments_endpoint(
    cohort_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await list_assignments(cohort_id, db, skip=skip, limit=limit)


@router.patch("/assignments/{assignment_id}/deactivate", response_model=AssignmentOut)
async def deactivate_assignment_endpoint(
    assignment_id: UUID,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await deactivate_assignment(assignment_id, db)


@router.post("/tutors", response_model=TutorOut, status_code=status.HTTP_201_CREATED)
async def create_tutor_endpoint(
    data: TutorCreate,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await create_tutor(data, db)


@router.get("/students", response_model=list[TutorOut])
async def list_students_endpoint(
    q: str | None = None,
    skip: int = 0,
    limit: int = 100,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Lista estudiantes activos, opcionalmente filtrados por nombre/email (q)."""
    from sqlalchemy import select as sa_select
    from app.models.user import User as UserModel
    safe_limit = max(1, min(limit, 100))
    query = sa_select(UserModel).where(
        UserModel.role == "student",
        UserModel.is_active.is_(True),
    )

    if q:
        term = f"%{q.strip()}%"
        query = query.where(
            UserModel.full_name.ilike(term) | UserModel.email.ilike(term)
        )

    result = await db.execute(
        query.order_by(UserModel.full_name.asc()).offset(skip).limit(safe_limit)
    )
    return list(result.scalars().all())


@router.get("/cohorts", response_model=list[CohortOut])
async def list_cohorts_endpoint(
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los cohortes disponibles."""
    return await list_cohorts(db)


@router.post("/cohorts", response_model=CohortOut, status_code=status.HTTP_201_CREATED)
async def create_cohort_endpoint(
    data: CohortCreate,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Crea una cohorte nueva."""
    return await create_cohort(data, db)


@router.patch("/cohorts/{cohort_id}", response_model=CohortOut)
async def update_cohort_endpoint(
    cohort_id: UUID,
    data: CohortUpdate,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza nombre y/o estado activo de una cohorte."""
    return await update_cohort(cohort_id, data, db)


@router.get("/tutors", response_model=list[TutorOut])
async def list_tutors_endpoint(
    skip: int = 0,
    limit: int = 20,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await list_tutors(db, skip=skip, limit=limit)


@router.patch("/tutors/{tutor_id}", response_model=TutorOut)
async def update_tutor_endpoint(
    tutor_id: UUID,
    body: TutorUpdate,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await update_tutor(tutor_id, body.full_name, body.is_active, db)


@router.patch("/students/{student_id}", response_model=TutorOut)
async def update_student_endpoint(
    student_id: UUID,
    body: TutorUpdate,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un estudiante (nombre y/o estado activo)."""
    from sqlalchemy import select as sa_select
    from app.models.user import User as UserModel
    from fastapi import HTTPException
    
    result = await db.execute(
        sa_select(UserModel).where(
            UserModel.id == student_id,
            UserModel.role == "student"
        )
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    if body.full_name is not None:
        student.full_name = body.full_name
    if body.is_active is not None:
        student.is_active = body.is_active
    
    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_endpoint(
    student_id: UUID,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Elimina un estudiante de la BD local y de Keycloak."""
    from sqlalchemy import select as sa_select, delete as sa_delete
    from app.models.user import User as UserModel
    from app.models.assignment import Assignment
    from app.models.logbook import LogbookEntry
    from app.models.attendance import AttendanceRecord
    from app.models.incident import Incident
    from app.models.wellbeing import WellbeingEntry
    from app.models.student_alert import StudentAlert
    from app.core.keycloak_client import delete_keycloak_user
    from fastapi import HTTPException
    
    result = await db.execute(
        sa_select(UserModel).where(
            UserModel.id == student_id,
            UserModel.role == "student"
        )
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # 1. Eliminar de Keycloak primero
    try:
        delete_keycloak_user(str(student_id))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar usuario de Keycloak: {str(e)}"
        )
    
    # 2. Eliminar registros relacionados en la BD
    await db.execute(sa_delete(StudentAlert).where(StudentAlert.student_id == student_id))
    await db.execute(sa_delete(WellbeingEntry).where(WellbeingEntry.student_id == student_id))
    await db.execute(sa_delete(Incident).where(Incident.student_id == student_id))
    await db.execute(sa_delete(AttendanceRecord).where(AttendanceRecord.student_id == student_id))
    await db.execute(sa_delete(LogbookEntry).where(LogbookEntry.student_id == student_id))
    await db.execute(sa_delete(Assignment).where(Assignment.student_id == student_id))
    
    # 3. Eliminar usuario de la BD
    await db.delete(student)
    await db.commit()


@router.delete("/tutors/{tutor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tutor_endpoint(
    tutor_id: UUID,
    _: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db),
):
    """Elimina un tutor de la BD local y de Keycloak. Las asignaciones se desactivan."""
    from sqlalchemy import select as sa_select
    from app.models.user import User as UserModel
    from app.models.assignment import Assignment
    from app.core.keycloak_client import delete_keycloak_user
    from fastapi import HTTPException
    
    result = await db.execute(
        sa_select(UserModel).where(
            UserModel.id == tutor_id,
            UserModel.role == "tutor"
        )
    )
    tutor = result.scalar_one_or_none()
    
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")
    
    # 1. Eliminar de Keycloak primero
    try:
        delete_keycloak_user(str(tutor_id))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar usuario de Keycloak: {str(e)}"
        )
    
    # 2. Desactivar asignaciones en lugar de eliminarlas
    assignments_result = await db.execute(
        sa_select(Assignment).where(Assignment.tutor_id == tutor_id)
    )
    for assignment in assignments_result.scalars():
        assignment.is_active = False
    
    # 3. Eliminar usuario de la BD
    await db.delete(tutor)
    await db.commit()
