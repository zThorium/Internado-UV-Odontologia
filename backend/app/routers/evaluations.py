from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.db.session import get_db
from app.schemas.auth import UserInToken
from app.schemas.evaluations import EvaluationCreate, EvaluationOut, StudentSummary
from app.services.evaluations import (
    get_assigned_students,
    submit_evaluation,
    get_student_evaluations,
)

router = APIRouter()


@router.get("/my-students", response_model=list[StudentSummary])
async def list_my_students(
    current_user: UserInToken = Depends(require_role("tutor")),
    db: AsyncSession = Depends(get_db),
):
    students = await get_assigned_students(UUID(current_user.id), db)
    return students


@router.post("", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation: EvaluationCreate,
    current_user: UserInToken = Depends(require_role("tutor")),
    db: AsyncSession = Depends(get_db),
):
    return await submit_evaluation(evaluation, current_user, db)


@router.get("/students/{student_id}", response_model=list[EvaluationOut])
async def list_student_evaluations(
    student_id: UUID,
    current_user: UserInToken = Depends(require_role("student", "tutor", "coordinator")),
    db: AsyncSession = Depends(get_db),
):
    return await get_student_evaluations(student_id, current_user, db)
