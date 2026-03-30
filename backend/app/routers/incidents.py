from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.db.session import get_db
from app.schemas.auth import UserInToken
from app.schemas.incidents import IncidentCreate, IncidentOut, IncidentStatusUpdate, IncidentResponseUpdate
from app.services.incidents import (
    submit_incident,
    get_incidents,
    update_incident_status,
    update_incident_response,
)

router = APIRouter()

_student_or_coordinator = Depends(require_role("student", "coordinator"))
_coordinator_only = Depends(require_role("coordinator"))


@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    current_user: UserInToken = _student_or_coordinator,
    db: AsyncSession = Depends(get_db),
):
    return await get_incidents(current_user, db)


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident: IncidentCreate,
    current_user: UserInToken = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    return await submit_incident(incident, current_user, db)


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: UUID,
    current_user: UserInToken = _student_or_coordinator,
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    from sqlalchemy import select
    from app.models.incident import Incident

    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    if current_user.role == "student" and str(incident.student_id) != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes ver incidentes de otro estudiante")

    return incident


@router.patch("/{incident_id}/status", response_model=IncidentOut)
async def change_incident_status(
    incident_id: UUID,
    status_update: IncidentStatusUpdate,
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    return await update_incident_status(incident_id, status_update, db)


@router.patch("/{incident_id}/response", response_model=IncidentOut)
async def add_coordinator_response(
    incident_id: UUID,
    response_update: IncidentResponseUpdate,
    current_user: UserInToken = _coordinator_only,
    db: AsyncSession = Depends(get_db),
):
    return await update_incident_response(incident_id, response_update.coordinator_response, db)
