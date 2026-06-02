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


def _serialize_evaluation(
    evaluation: Evaluation,
    student_name: str | None,
    tutor_name: str | None,
    clinical_site: str | None,
) -> dict:
    item_count = len(evaluation.items)
    average_score = None
    if item_count > 0:
        average_score = round(sum(item.score for item in evaluation.items) / item_count, 2)

    return {
        "id": evaluation.id,
        "tutor_id": evaluation.tutor_id,
        "student_id": evaluation.student_id,
        "assignment_id": evaluation.assignment_id,
        "period_label": evaluation.period_label,
        "student_name": student_name,
        "tutor_name": tutor_name,
        "clinical_site": clinical_site,
        "average_score": average_score,
        "overall_comment": evaluation.overall_comment,
        "created_at": evaluation.created_at,
        "items": evaluation.items,
    }


async def get_assigned_students(tutor_id: UUID, db: AsyncSession) -> list[dict]:
    """
    Retorna lista de estudiantes asignados al tutor con asignaciones activas.
    JOIN entre Assignment y User (student).
    """
    tutor_name = await db.scalar(
        select(User.full_name).where(User.id == tutor_id)
    )

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
            "tutor_name": tutor_name,
            "clinical_site": row.Assignment.clinical_site,
            "assignment_id": str(row.Assignment.id),
        }
        for row in rows
    ]


async def submit_evaluation(
    evaluation: EvaluationCreate,
    current_user: UserInToken,
    db: AsyncSession,
) -> dict:
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

    duplicate_result = await db.execute(
        select(Evaluation).where(
            Evaluation.assignment_id == evaluation.assignment_id,
            Evaluation.period_label == evaluation.period_label,
        )
    )
    if duplicate_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una evaluación registrada para este periodo",
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

    try:
        from app.services.alerts import run_alert_evaluation
        await run_alert_evaluation(db)
    except Exception:
        pass

    tutor_name = await db.scalar(
        select(User.full_name).where(User.id == tutor_id)
    )

    # Recargar con items y datos de contexto
    result = await db.execute(
        select(Evaluation, User, Assignment)
        .options(selectinload(Evaluation.items))
        .join(User, User.id == Evaluation.student_id)
        .join(Assignment, Assignment.id == Evaluation.assignment_id)
        .where(Evaluation.id == eval_obj.id)
    )
    row = result.one()
    return _serialize_evaluation(
        row.Evaluation,
        student_name=row.User.full_name,
        tutor_name=tutor_name,
        clinical_site=row.Assignment.clinical_site,
    )


async def get_student_evaluations(
    student_id: UUID,
    current_user: UserInToken,
    db: AsyncSession,
) -> list[dict]:
    """
    Control de acceso:
    - student: solo puede ver sus propias evaluaciones
    - tutor: solo evaluaciones donde tutor_id == current_user.id AND student_id == student_id
    - coordinator: puede ver todas las evaluaciones del estudiante
    """
    if current_user.role == "student" and str(student_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes ver tus propias evaluaciones")

    query = (
        select(Evaluation, Assignment)
        .options(selectinload(Evaluation.items))
        .join(Assignment, Assignment.id == Evaluation.assignment_id)
        .where(Evaluation.student_id == student_id)
        .order_by(Evaluation.created_at.desc())
    )

    if current_user.role == "tutor":
        tutor_id = uuid.UUID(current_user.id)
        query = query.where(Evaluation.tutor_id == tutor_id)

    rows = (await db.execute(query)).all()
    if not rows:
        return []

    student_name = await db.scalar(
        select(User.full_name).where(User.id == student_id)
    )

    tutor_ids = {row.Evaluation.tutor_id for row in rows}
    tutors_result = await db.execute(
        select(User.id, User.full_name).where(User.id.in_(tutor_ids))
    )
    tutor_names = {row.id: row.full_name for row in tutors_result.all()}

    return [
        _serialize_evaluation(
            row.Evaluation,
            student_name=student_name,
            tutor_name=tutor_names.get(row.Evaluation.tutor_id),
            clinical_site=row.Assignment.clinical_site,
        )
        for row in rows
    ]
