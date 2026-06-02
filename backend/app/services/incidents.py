import logging
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incidents import (
    IncidentCreate,
    IncidentStatusUpdate,
    TutorIncidentCreate,
)
from app.schemas.auth import UserInToken
from app.services.email import send_incident_notification

logger = logging.getLogger(__name__)


async def submit_incident(
    incident: IncidentCreate,
    current_user: UserInToken,
    db: AsyncSession,
) -> Incident:
    """
    Crea un incidente con student_id = current_user.id y status = "submitted".
    Después del commit, envía notificación de forma no bloqueante.
    Si el email falla, loguea el error pero NO lanza excepción.
    """
    incident_obj = Incident(
        student_id=UUID(current_user.id),
        reported_by_user_id=None,
        reporter_role="student",
        incident_type=incident.incident_type,
        urgency_level="medium",
        description=incident.description,
        event_date=incident.event_date,
        status="submitted",
    )
    db.add(incident_obj)
    await db.commit()

    # Recargar para obtener valores generados por el servidor (created_at, updated_at)
    await db.refresh(incident_obj)

    try:
        await send_incident_notification(current_user.id, incident.incident_type)
    except Exception as exc:
        logger.error(
            "Error sending incident notification for student=%s: %s",
            current_user.id,
            exc,
        )

    return incident_obj


async def submit_incident_as_tutor(
    incident: TutorIncidentCreate,
    current_user: UserInToken,
    db: AsyncSession,
) -> Incident:
    """
    Crea un incidente levantado por tutor para un estudiante asignado activamente.
    """
    tutor_id = UUID(current_user.id)

    assignment_result = await db.execute(
        select(Assignment).where(
            Assignment.tutor_id == tutor_id,
            Assignment.student_id == incident.student_id,
            Assignment.is_active.is_(True),
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes reportar incidentes para estudiantes asignados activamente",
        )

    incident_obj = Incident(
        student_id=incident.student_id,
        reported_by_user_id=tutor_id,
        reporter_role="tutor",
        title=incident.title.strip(),
        incident_type="other",
        urgency_level=incident.urgency_level,
        description=incident.description,
        event_date=incident.event_date,
        status="submitted",
    )
    db.add(incident_obj)
    await db.commit()
    await db.refresh(incident_obj)

    try:
        await send_incident_notification(str(incident.student_id), incident_obj.incident_type)
    except Exception as exc:
        logger.error(
            "Error sending tutor incident notification for student=%s: %s",
            incident.student_id,
            exc,
        )

    return incident_obj


def _serialize_incident(
    incident: Incident,
    student_name: str | None = None,
    student_email: str | None = None,
    reporter_name: str | None = None,
) -> dict:
    return {
        "id": incident.id,
        "student_id": incident.student_id,
        "reported_by_user_id": incident.reported_by_user_id,
        "reporter_role": incident.reporter_role,
        "title": incident.title,
        "student_name": student_name,
        "student_email": student_email,
        "reporter_name": reporter_name,
        "incident_type": incident.incident_type,
        "urgency_level": incident.urgency_level,
        "description": incident.description,
        "event_date": incident.event_date,
        "status": incident.status,
        "coordinator_response": incident.coordinator_response,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
    }


async def get_incidents(
    current_user: UserInToken,
    db: AsyncSession,
) -> list[dict]:
    """
    - student: retorna solo sus propios incidentes
    - coordinator: retorna todos con info del estudiante, ordenados por created_at DESC
    """
    if current_user.role == "student":
        result = await db.execute(
            select(Incident)
            .where(
                Incident.student_id == UUID(current_user.id),
                Incident.reporter_role == "student",
            )
            .order_by(Incident.created_at.desc())
        )
        incidents = list(result.scalars().all())
        return [_serialize_incident(incident) for incident in incidents]

    StudentUser = aliased(User, flat=True)
    ReporterUser = aliased(User, flat=True)

    query = (
        select(Incident, StudentUser, ReporterUser)
        .join(StudentUser, Incident.student_id == StudentUser.id)
        .outerjoin(ReporterUser, Incident.reported_by_user_id == ReporterUser.id)
        .order_by(Incident.created_at.desc())
    )

    if current_user.role == "tutor":
        query = query.where(
            Incident.reporter_role == "tutor",
            Incident.reported_by_user_id == UUID(current_user.id),
        )

    result = await db.execute(query)
    rows = result.all()
    return [
        _serialize_incident(
            incident,
            student_name=student.full_name,
            student_email=student.email,
            reporter_name=reporter.full_name if reporter else None,
        )
        for incident, student, reporter in rows
    ]


async def update_incident_status(
    incident_id: UUID,
    status_update: IncidentStatusUpdate,
    db: AsyncSession,
) -> Incident:
    """
    Actualiza el status de un incidente.
    - Si no existe → 404
    """
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    incident.status = status_update.status
    incident.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(incident)

    return incident


async def update_incident_response(
    incident_id: UUID,
    response: str,
    db: AsyncSession,
) -> Incident:
    """
    Actualiza la respuesta del coordinador para un incidente.
    - Si no existe → 404
    """
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    incident.coordinator_response = response
    incident.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(incident)

    return incident
