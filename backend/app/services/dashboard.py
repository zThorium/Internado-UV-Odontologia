from uuid import UUID
from datetime import datetime, timedelta, timezone, time

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.security import hash_password
from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.logbook import LogbookEntry
from app.models.evaluation import Evaluation
from app.models.student_alert import StudentAlert
from app.models.user import User
from app.schemas.dashboard import AssignmentCreate, TutorCreate
from app.services.email import send_welcome_email


async def get_dashboard_overview(
    cohort_id: UUID | None,
    db: AsyncSession,
) -> dict:
    # Conteos de usuarios (no dependen de cohort)
    total_students = await db.scalar(
        select(func.count()).select_from(User).where(User.role == "student")
    )
    total_tutors = await db.scalar(
        select(func.count()).select_from(User).where(User.role == "tutor")
    )

    # Logbook entries
    entries_q = select(func.count()).select_from(LogbookEntry)
    pending_q = select(func.count()).select_from(LogbookEntry).where(
        LogbookEntry.status.in_(["draft", "submitted"])
    )
    if cohort_id is not None:
        entries_q = entries_q.where(LogbookEntry.cohort_id == cohort_id)
        pending_q = pending_q.where(LogbookEntry.cohort_id == cohort_id)

    total_entries = await db.scalar(entries_q)
    pending_entries = await db.scalar(pending_q)

    # Incidents (no tienen cohort_id directo; si cohort_id se provee, filtrar via assignments)
    incidents_q = select(func.count()).select_from(Incident)
    open_q = select(func.count()).select_from(Incident).where(
        Incident.status.in_(["submitted", "under_review"])
    )
    if cohort_id is not None:
        student_ids_q = select(Assignment.student_id).where(
            Assignment.cohort_id == cohort_id
        )
        incidents_q = incidents_q.where(Incident.student_id.in_(student_ids_q))
        open_q = open_q.where(Incident.student_id.in_(student_ids_q))

    total_incidents = await db.scalar(incidents_q)
    open_incidents = await db.scalar(open_q)

    return {
        "total_students": total_students or 0,
        "total_tutors": total_tutors or 0,
        "total_entries": total_entries or 0,
        "pending_entries": pending_entries or 0,
        "total_incidents": total_incidents or 0,
        "open_incidents": open_incidents or 0,
    }


async def create_assignment(data: AssignmentCreate, db: AsyncSession) -> Assignment:
    assignment = Assignment(
        student_id=data.student_id,
        tutor_id=data.tutor_id,
        cohort_id=data.cohort_id,
        care_level=data.care_level,
        clinical_site=data.clinical_site,
        start_date=data.start_date,
        end_date=data.end_date,
        is_active=True,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_assignments(
    cohort_id: UUID | None,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> list[dict]:
    StudentAlias = aliased(User, flat=True)
    TutorAlias = aliased(User, flat=True)

    q = (
        select(Assignment, StudentAlias.full_name, TutorAlias.full_name)
        .join(StudentAlias, Assignment.student_id == StudentAlias.id)
        .join(TutorAlias, Assignment.tutor_id == TutorAlias.id)
    )
    if cohort_id is not None:
        q = q.where(Assignment.cohort_id == cohort_id)
    q = q.order_by(Assignment.start_date.desc()).offset(skip).limit(limit)

    result = await db.execute(q)
    rows = result.all()

    assignments = []
    for row in rows:
        a, student_name, tutor_name = row[0], row[1], row[2]
        assignments.append({
            "id": a.id,
            "student_id": a.student_id,
            "tutor_id": a.tutor_id,
            "cohort_id": a.cohort_id,
            "care_level": a.care_level,
            "clinical_site": a.clinical_site,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "is_active": a.is_active,
            "student_name": student_name,
            "tutor_name": tutor_name,
        })
    return assignments


async def deactivate_assignment(assignment_id: UUID, db: AsyncSession) -> Assignment:
    assignment = await db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
    assignment.is_active = False
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def create_tutor(data: TutorCreate, db: AsyncSession) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )
    tutor = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role="tutor",
        is_active=True,
    )
    db.add(tutor)
    await db.commit()
    await db.refresh(tutor)
    try:
        await send_welcome_email(data.email, data.full_name)
    except Exception:
        pass
    return tutor


async def list_tutors(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> list[User]:
    q = (
        select(User)
        .where(User.role == "tutor")
        .order_by(User.full_name.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_tutor(
    tutor_id: UUID,
    full_name: str | None,
    is_active: bool | None,
    db: AsyncSession,
) -> User:
    tutor = await db.get(User, tutor_id)
    if tutor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor no encontrado")
    if full_name is not None:
        tutor.full_name = full_name
    if is_active is not None:
        tutor.is_active = is_active
    await db.commit()
    await db.refresh(tutor)
    return tutor


async def get_dashboard_trends(db: AsyncSession) -> dict:
    """
    Retorna deltas comparativos de esta semana vs la semana anterior.
    Delta positivo: subió respecto al periodo anterior.
    Delta negativo: bajó respecto al periodo anterior.
    """
    now = datetime.now(timezone.utc)
    start_current = now - timedelta(days=7)
    start_previous = now - timedelta(days=14)

    async def _weekly_delta(stmt_current, stmt_previous) -> int:
        current = (await db.scalar(stmt_current)) or 0
        previous = (await db.scalar(stmt_previous)) or 0
        return int(current) - int(previous)

    return {
        "total_students": await _weekly_delta(
            select(func.count()).select_from(User).where(
                User.role == "student",
                User.created_at >= start_current,
            ),
            select(func.count()).select_from(User).where(
                User.role == "student",
                User.created_at >= start_previous,
                User.created_at < start_current,
            ),
        ),
        "total_tutors": await _weekly_delta(
            select(func.count()).select_from(User).where(
                User.role == "tutor",
                User.created_at >= start_current,
            ),
            select(func.count()).select_from(User).where(
                User.role == "tutor",
                User.created_at >= start_previous,
                User.created_at < start_current,
            ),
        ),
        "total_entries": await _weekly_delta(
            select(func.count()).select_from(LogbookEntry).where(
                LogbookEntry.created_at >= start_current,
            ),
            select(func.count()).select_from(LogbookEntry).where(
                LogbookEntry.created_at >= start_previous,
                LogbookEntry.created_at < start_current,
            ),
        ),
        "pending_entries": await _weekly_delta(
            select(func.count()).select_from(LogbookEntry).where(
                LogbookEntry.created_at >= start_current,
                LogbookEntry.status.in_(["draft", "submitted"]),
            ),
            select(func.count()).select_from(LogbookEntry).where(
                LogbookEntry.created_at >= start_previous,
                LogbookEntry.created_at < start_current,
                LogbookEntry.status.in_(["draft", "submitted"]),
            ),
        ),
        "total_incidents": await _weekly_delta(
            select(func.count()).select_from(Incident).where(
                Incident.created_at >= start_current,
            ),
            select(func.count()).select_from(Incident).where(
                Incident.created_at >= start_previous,
                Incident.created_at < start_current,
            ),
        ),
        "open_incidents": await _weekly_delta(
            select(func.count()).select_from(Incident).where(
                Incident.created_at >= start_current,
                Incident.status.in_(["submitted", "under_review"]),
            ),
            select(func.count()).select_from(Incident).where(
                Incident.created_at >= start_previous,
                Incident.created_at < start_current,
                Incident.status.in_(["submitted", "under_review"]),
            ),
        ),
    }


async def get_recent_activity(db: AsyncSession, limit: int = 5) -> list[dict]:
    """Construye un feed consolidado con acciones recientes del sistema."""
    StudentAlias = aliased(User, flat=True)
    safe_limit = max(1, min(limit, 20))

    logbook_rows = (
        await db.execute(
            select(LogbookEntry.id, LogbookEntry.student_id, LogbookEntry.created_at, StudentAlias.full_name)
            .join(StudentAlias, StudentAlias.id == LogbookEntry.student_id)
            .order_by(LogbookEntry.created_at.desc())
            .limit(safe_limit)
        )
    ).all()

    evaluation_rows = (
        await db.execute(
            select(Evaluation.id, Evaluation.student_id, Evaluation.created_at, StudentAlias.full_name)
            .join(StudentAlias, StudentAlias.id == Evaluation.student_id)
            .order_by(Evaluation.created_at.desc())
            .limit(safe_limit)
        )
    ).all()

    incident_new_rows = (
        await db.execute(
            select(Incident.id, Incident.student_id, Incident.created_at, StudentAlias.full_name)
            .join(StudentAlias, StudentAlias.id == Incident.student_id)
            .order_by(Incident.created_at.desc())
            .limit(safe_limit)
        )
    ).all()

    incident_update_rows = (
        await db.execute(
            select(Incident.id, Incident.student_id, Incident.updated_at, Incident.status, StudentAlias.full_name)
            .join(StudentAlias, StudentAlias.id == Incident.student_id)
            .where(Incident.updated_at > Incident.created_at)
            .order_by(Incident.updated_at.desc())
            .limit(safe_limit)
        )
    ).all()

    status_label = {
        "submitted": "enviado",
        "under_review": "en revisión",
        "resolved": "resuelto",
    }

    events: list[dict] = []

    for row in logbook_rows:
        events.append({
            "id": f"logbook:{row.id}",
            "kind": "logbook_created",
            "level": "normal",
            "student_id": row.student_id,
            "student_name": row.full_name,
            "description": "Nuevo registro de bitácora",
            "occurred_at": row.created_at,
        })

    for row in evaluation_rows:
        events.append({
            "id": f"evaluation:{row.id}",
            "kind": "evaluation_created",
            "level": "normal",
            "student_id": row.student_id,
            "student_name": row.full_name,
            "description": "Nueva evaluación de tutor",
            "occurred_at": row.created_at,
        })

    for row in incident_new_rows:
        events.append({
            "id": f"incident-new:{row.id}",
            "kind": "incident_created",
            "level": "critical",
            "student_id": row.student_id,
            "student_name": row.full_name,
            "description": "Nuevo reporte de incidente",
            "occurred_at": row.created_at,
        })

    for row in incident_update_rows:
        events.append({
            "id": f"incident-status:{row.id}:{row.updated_at}",
            "kind": "incident_status_changed",
            "level": "normal",
            "student_id": row.student_id,
            "student_name": row.full_name,
            "description": f"Cambio de estado de incidente a {status_label.get(row.status, row.status)}",
            "occurred_at": row.updated_at,
        })

    events.sort(key=lambda e: e["occurred_at"], reverse=True)
    return events[:safe_limit]


async def get_wellbeing_quick(db: AsyncSession, limit: int = 3) -> dict:
    """Retorna estudiantes con alertas activas recientes para vista rápida."""
    StudentAlias = aliased(User, flat=True)
    safe_limit = max(1, min(limit, 10))

    total_active = (await db.scalar(
        select(func.count()).select_from(StudentAlert).where(StudentAlert.is_active.is_(True))
    )) or 0

    rows = (
        await db.execute(
            select(
                StudentAlert.id,
                StudentAlert.student_id,
                StudentAlert.alert_level,
                StudentAlert.alert_type,
                StudentAlert.triggered_at,
                StudentAlias.full_name,
            )
            .join(StudentAlias, StudentAlias.id == StudentAlert.student_id)
            .where(StudentAlert.is_active.is_(True))
            .order_by(StudentAlert.triggered_at.desc())
            .limit(safe_limit)
        )
    ).all()

    return {
        "total_active": total_active,
        "items": [
            {
                "student_id": row.student_id,
                "student_name": row.full_name,
                "alert_level": row.alert_level,
                "alert_type": row.alert_type,
                "triggered_at": row.triggered_at,
            }
            for row in rows
        ],
    }


async def get_dashboard_metric_series(db: AsyncSession) -> dict:
    """Retorna 4 puntos semanales (incluida semana actual) para métricas del dashboard."""
    today = datetime.now(timezone.utc).date()
    current_monday = today - timedelta(days=today.weekday())
    week_starts = [current_monday - timedelta(days=7 * i) for i in reversed(range(4))]

    def _week_label(index: int) -> str:
        if index == len(week_starts) - 1:
            return "Actual"
        return f"S-{len(week_starts) - 1 - index}"

    series = {
        "total_students": [],
        "total_entries": [],
        "open_incidents": [],
        "pending_entries": [],
    }

    for idx, week_start in enumerate(week_starts):
        week_end = datetime.combine(week_start + timedelta(days=7), time.min, tzinfo=timezone.utc)

        students_value = (await db.scalar(
            select(func.count()).select_from(User).where(
                User.role == "student",
                User.is_active.is_(True),
                User.created_at < week_end,
            )
        )) or 0

        entries_value = (await db.scalar(
            select(func.count()).select_from(LogbookEntry).where(
                LogbookEntry.created_at < week_end,
            )
        )) or 0

        open_incidents_value = (await db.scalar(
            select(func.count()).select_from(Incident).where(
                Incident.created_at < week_end,
                Incident.status.in_(["submitted", "under_review"]),
            )
        )) or 0

        pending_entries_value = (await db.scalar(
            select(func.count()).select_from(LogbookEntry).where(
                LogbookEntry.created_at < week_end,
                LogbookEntry.status.in_(["draft", "submitted"]),
            )
        )) or 0

        label = _week_label(idx)
        series["total_students"].append({"label": label, "value": int(students_value)})
        series["total_entries"].append({"label": label, "value": int(entries_value)})
        series["open_incidents"].append({"label": label, "value": int(open_incidents_value)})
        series["pending_entries"].append({"label": label, "value": int(pending_entries_value)})

    return {
        "series": [
            {"key": "total_students", "points": series["total_students"]},
            {"key": "total_entries", "points": series["total_entries"]},
            {"key": "open_incidents", "points": series["open_incidents"]},
            {"key": "pending_entries", "points": series["pending_entries"]},
        ]
    }
