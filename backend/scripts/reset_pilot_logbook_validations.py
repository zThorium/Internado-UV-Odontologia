"""
Elimina validaciones de tutor en bitácoras de estudiantes demo del piloto.

Permite que tutoras reales (Marjorie, Karina) prueben el botón Validar.

Uso:
    ALLOW_RESET_VALIDATIONS=1 python -m scripts.reset_pilot_logbook_validations
    ALLOW_RESET_VALIDATIONS=1 python -m scripts.reset_pilot_logbook_validations --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models.logbook import LogbookEntry
from app.models.logbook_validation import LogbookValidation
from app.models.user import User

DEFAULT_STUDENT_EMAILS = [
    "estudiante01@demo.internado-uv.cl",
    "estudiante02@demo.internado-uv.cl",
    "estudiante03@demo.internado-uv.cl",
    "estudiante04@demo.internado-uv.cl",
]


def _require_allowed() -> None:
    if os.getenv("ALLOW_RESET_VALIDATIONS") != "1":
        print(
            "[reset] Abortado: define ALLOW_RESET_VALIDATIONS=1 para ejecutar.",
            file=sys.stderr,
        )
        sys.exit(1)


async def reset_validations(*, emails: list[str], dry_run: bool) -> None:
    _require_allowed()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email.in_(emails)))
        students = list(result.scalars().all())
        found_emails = {s.email for s in students}
        missing = [e for e in emails if e not in found_emails]
        for email in missing:
            print(f"[warn]    estudiante no encontrado: {email}")

        if not students:
            print("[reset] No hay estudiantes que procesar.")
            return

        student_ids = [s.id for s in students]
        entries_result = await session.execute(
            select(LogbookEntry.id).where(LogbookEntry.student_id.in_(student_ids))
        )
        entry_ids = [row[0] for row in entries_result.fetchall()]

        if not entry_ids:
            print("[reset] Sin entradas de bitácora para esos estudiantes.")
            return

        validations_result = await session.execute(
            select(LogbookValidation).where(LogbookValidation.entry_id.in_(entry_ids))
        )
        validations = list(validations_result.scalars().all())

        print(f"[reset] Estudiantes: {len(students)} | Entradas: {len(entry_ids)} | Validaciones a borrar: {len(validations)}")

        if dry_run:
            for v in validations:
                print(f"[dry-run] borraría validación entry_id={v.entry_id} tutor_id={v.tutor_id}")
            return

        if not validations:
            print("[reset] Nada que borrar.")
            return

        await session.execute(
            delete(LogbookValidation).where(LogbookValidation.entry_id.in_(entry_ids))
        )
        await session.commit()
        print(f"[reset] Eliminadas {len(validations)} validaciones.")

        try:
            from app.services.alerts import run_alert_evaluation

            summary = await run_alert_evaluation(session)
            print(f"[reset] Alertas re-evaluadas: {summary}")
        except Exception as exc:
            print(f"[warn]    No se pudo re-evaluar alertas: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quitar validaciones de tutor en bitácoras demo del piloto tesis"
    )
    parser.add_argument(
        "--email",
        action="append",
        dest="emails",
        help="Email de estudiante (repetible). Default: estudiante01-04 @demo",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    emails = args.emails if args.emails else DEFAULT_STUDENT_EMAILS
    asyncio.run(reset_validations(emails=[e.strip().lower() for e in emails], dry_run=args.dry_run))


if __name__ == "__main__":
    main()
