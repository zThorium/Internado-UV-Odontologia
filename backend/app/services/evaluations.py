import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.assignment import Assignment
from app.models.user import User
from app.models.evaluation import Evaluation, EvaluationItem
from app.schemas.evaluations import EvaluationCreate
from app.schemas.auth import UserInToken


async def get_assigned_students(tutor_id: UUID, db: AsyncSession) -> list[dict]:
    """
    Retorna lista de estudiantes asignados al tutor con asignaciones activas.
    JOIN entre Assignment y User (student).
    """
    result = await db.execute(
        select(Assignment, User)
        .join(User, User.id == Assignment.student_id)
        .where(
            Assignment.tutor_id == tutor_id,
            Assignment.is_active == True,  # noqa: E712
        )
    )
    rows = result.all()
    return [
        {
            "id": str(row.User.id),
            "full_name": row.User.full_name,
            "email": row.User.email,
            "clinical_site": row.Assignment.clinical_site,
            "assignment_id": str(row.Assignment.id),
        }
        for row in rows
    ]


async def submit_evaluation(
    evaluation: EvaluationCreate,
    current_user: UserInToken,
    db: AsyncSession,
) -> Evaluation:
    """
    Verifica asignación activa tutor↔estudiante, crea Evaluation + EvaluationItems.
    """
    tutor_id = uuid.UUID(current_user.id)

    # Verificar asignación activa
    result = await db.execute(
        select(Assignment).where(
            Assignment.tutor_id == tutor_id,
            Assignment.student_id == evaluation.student_id,
            Assignment.id == evaluation.assignment_id,
            Assignment.is_active == True,  # noqa: E712
        )
    )
    assignment = result.scalar_one_or_none()

    if assignment is None:
        raise HTTPException(
            status_code=403,
            detail="No tienes asignación activa con este estudiante",
        )

    # Crear Evaluation
    eval_obj = Evaluation(
        tutor_id=tutor_id,
        student_id=evaluation.student_id,
        assignment_id=evaluation.assignment_id,
        period_label=evaluation.period_label,
        overall_comment=evaluation.overall_comment,
    )
    db.add(eval_obj)
    await db.flush()

    # Crear EvaluationItems
    for item in evaluation.items:
        eval_item = EvaluationItem(
            evaluation_id=eval_obj.id,
            dimension=item.dimension,
            score=item.score,
            comment=item.comment,
        )
        db.add(eval_item)

    await db.commit()

    # Recargar con items
    result = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.items))
        .where(Evaluation.id == eval_obj.id)
    )
    return result.scalar_one()


async def get_student_evaluations(
    student_id: UUID,
    current_user: UserInToken,
    db: AsyncSession,
) -> list[Evaluation]:
    """
    Control de acceso:
    - student: solo puede ver sus propias evaluaciones
    - tutor: solo evaluaciones donde tutor_id == current_user.id AND student_id == student_id
    - coordinator: puede ver todas las evaluaciones del estudiante
    """
    if current_user.role == "student" and str(student_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes ver tus propias evaluaciones")

    query = (
        select(Evaluation)
        .options(selectinload(Evaluation.items))
        .where(Evaluation.student_id == student_id)
        .order_by(Evaluation.created_at.desc())
    )

    if current_user.role == "tutor":
        tutor_id = uuid.UUID(current_user.id)
        query = query.where(Evaluation.tutor_id == tutor_id)

    result = await db.execute(query)
    return list(result.scalars().all())
