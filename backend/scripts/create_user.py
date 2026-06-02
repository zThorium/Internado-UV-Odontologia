"""
Alta de usuarios en DB + Keycloak (cualquier rol).

Ejemplos:
    python -m scripts.create_user \\
      --email nombre@uv.cl \\
      --name "Nombre Apellido" \\
      --role student \\
      --password "TemporalSegura123"

    python -m scripts.create_user --email t@uv.cl --name "Tutor" --role tutor --password "x" --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from scripts.seed_utils import SeedUserSpec, connect_keycloak_admin, ensure_user_in_db_and_keycloak
from app.db.session import AsyncSessionLocal

VALID_ROLES = ("student", "tutor", "coordinator")


async def create_user(
    *,
    email: str,
    full_name: str,
    role: str,
    password: str,
    dry_run: bool = False,
    skip_onboarding: bool = False,
) -> None:
    if role not in VALID_ROLES:
        print(f"[create_user] Rol inválido: {role}. Use: {', '.join(VALID_ROLES)}", file=sys.stderr)
        sys.exit(1)

    spec = SeedUserSpec(email=email, password=password, full_name=full_name, role=role)  # type: ignore[arg-type]

    if dry_run:
        print(f"[dry-run] Crearía usuario {email} ({role}) — {full_name}")
        return

    keycloak_admin = connect_keycloak_admin()
    async with AsyncSessionLocal() as session:
        await ensure_user_in_db_and_keycloak(
            session,
            keycloak_admin,
            spec,
            mark_onboarding_complete=not skip_onboarding,
        )
        await session.commit()
    print(f"[create_user] Listo: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear usuario en DB y Keycloak")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="Nombre completo")
    parser.add_argument("--role", required=True, choices=VALID_ROLES)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--require-onboarding",
        action="store_true",
        help="Dejar has_completed_onboarding=false (tour en primer login)",
    )
    args = parser.parse_args()

    asyncio.run(
        create_user(
            email=args.email.strip().lower(),
            full_name=args.name.strip(),
            role=args.role,
            password=args.password,
            dry_run=args.dry_run,
            skip_onboarding=args.require_onboarding,
        )
    )


if __name__ == "__main__":
    main()
