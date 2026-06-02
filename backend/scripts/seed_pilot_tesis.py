"""
Configura cohorte Piloto Tesis 2026 y assignments desde CSV.

CSV (docs/testing/data/pilot-users.example.csv):
    email,full_name,role,password,student_email,tutor_email,clinical_site,care_level

Filas con role=student|tutor|coordinator crean usuarios.
Filas con student_email+tutor_email crean assignment (emails deben existir).

Ejemplo:
    python -m scripts.seed_pilot_tesis --csv ../docs/testing/data/pilot-users.csv
    python -m scripts.seed_pilot_tesis --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.assignment import Assignment
from app.models.cohort import Cohort
from app.models.user import User
from scripts.seed_utils import SeedUserSpec, connect_keycloak_admin, ensure_user_in_db_and_keycloak

COHORT_NAME = "Piloto Tesis 2026"
DEFAULT_CSV = Path(__file__).resolve().parents[2] / "docs/testing/data/pilot-users.example.csv"


async def _ensure_cohort(session) -> Cohort:
    result = await session.execute(select(Cohort).where(Cohort.name == COHORT_NAME))
    cohort = result.scalar_one_or_none()
    if cohort:
        print(f"[skip]    cohorte '{COHORT_NAME}' ya existe")
        return cohort
    cohort = Cohort(name=COHORT_NAME, year=2026, semester=1, is_active=True)
    session.add(cohort)
    await session.flush()
    print(f"[created] cohorte '{COHORT_NAME}' ({cohort.id})")
    return cohort


async def _user_by_email(session, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.strip().lower()))
    return result.scalar_one_or_none()


async def seed_pilot_tesis(*, csv_path: Path, dry_run: bool) -> None:
    if not csv_path.is_file():
        print(f"[seed_pilot_tesis] No existe CSV: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with csv_path.open(encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))

    if dry_run:
        print(f"[dry-run] {len(rows)} filas en {csv_path}")
        for row in rows:
            role = (row.get("role") or "").strip()
            if role:
                print(f"  usuario: {row.get('email')} ({role})")
            elif row.get("student_email") and row.get("tutor_email"):
                print(f"  assignment: {row.get('student_email')} -> {row.get('tutor_email')}")
        return

    keycloak_admin = connect_keycloak_admin()
    today = date.today()

    async with AsyncSessionLocal() as session:
        cohort = await _ensure_cohort(session)

        for row in rows:
            role = (row.get("role") or "").strip()
            email = (row.get("email") or "").strip().lower()
            if not role or not email:
                continue
            password = (row.get("password") or "").strip()
            if not password:
                print(f"[warn]    sin password para {email}; omitido")
                continue
            await ensure_user_in_db_and_keycloak(
                session,
                keycloak_admin,
                SeedUserSpec(
                    email=email,
                    password=password,
                    full_name=(row.get("full_name") or email).strip(),
                    role=role,  # type: ignore[arg-type]
                ),
            )

        await session.flush()

        for row in rows:
            student_email = (row.get("student_email") or "").strip().lower()
            tutor_email = (row.get("tutor_email") or "").strip().lower()
            if not student_email or not tutor_email:
                continue

            student = await _user_by_email(session, student_email)
            tutor = await _user_by_email(session, tutor_email)
            if not student or not tutor:
                print(f"[warn]    assignment omitido: falta usuario {student_email} o {tutor_email}")
                continue

            existing = await session.execute(
                select(Assignment).where(
                    Assignment.student_id == student.id,
                    Assignment.cohort_id == cohort.id,
                    Assignment.is_active.is_(True),
                )
            )
            if existing.scalar_one_or_none():
                print(f"[skip]    assignment {student_email} ya existe")
                continue

            site = (row.get("clinical_site") or "Campo clínico piloto").strip()
            care = (row.get("care_level") or "primary").strip()
            if care not in ("primary", "secondary", "tertiary"):
                care = "primary"

            session.add(
                Assignment(
                    student_id=student.id,
                    tutor_id=tutor.id,
                    cohort_id=cohort.id,
                    clinical_site=site,
                    care_level=care,
                    start_date=today - timedelta(days=30),
                    end_date=today + timedelta(days=120),
                    is_active=True,
                )
            )
            print(f"[created] assignment {student_email} -> {tutor_email} @ {site}")

        await session.commit()

    print("\n✓ Piloto Tesis configurado")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cohort Piloto Tesis 2026 + usuarios CSV")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed_pilot_tesis(csv_path=args.csv, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
