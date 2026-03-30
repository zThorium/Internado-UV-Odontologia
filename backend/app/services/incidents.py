import logging
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.incident import Incident
from app.schemas.incidents import IncidentCreate, IncidentStatusUpdate
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
        incident_type=incident.incident_type,
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


async def get_incidents(
    current_user: UserInToken,
    db: AsyncSession,
) -> list[dict]:
    """
    - student: retorna solo sus propios incidentes
    - coordinator: retorna todos con info del estudiante, ordenados por created_at DESC
    """
    from app.models.user import User
    from sqlalchemy.orm import selectinload
    
    if current_user.role == "student":
        result = await db.execute(
            select(Incident).where(Incident.student_id == UUID(current_user.id))
        )
        incidents = list(result.scalars().all())
        # Students don't need student info in their own incidents
        return [
            {
                **incident.__dict__,
                "student_name": None,
                "student_email": None,
            }
            for incident in incidents
        ]
    else:
        # Coordinator gets all incidents with student info
        result = await db.execute(
            select(Incident, User)
            .join(User, Incident.student_id == User.id)
            .order_by(Incident.created_at.desc())
        )
        rows = result.all()
        return [
            {
                **incident.__dict__,
                "student_name": user.full_name,
                "student_email": user.email,
            }
            for incident, user in rows
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
