"""
Script de seed para datos iniciales de desarrollo.

Ejecutar desde el directorio backend/:
    python -m scripts.seed

Crea:
    - 1 cohorte activa (Internado 2026-1)
    - 3 usuarios: coordinador, tutor, estudiante (en DB y Keycloak)
    - 1 assignment: estudiante → tutor, en Hospital Base Valdivia, cohorte 2026-1

Credenciales:
    coordinador: coord@internado-uv.cl / coord123
    tutor:       tutor@internado-uv.cl / tutor123
    estudiante:  estudiante@internado-uv.cl / estudiante123
"""

import asyncio
import uuid
import subprocess
from pathlib import Path
from datetime import date

from sqlalchemy import select
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.cohort import Cohort
from app.models.assignment import Assignment
from app.core.security import hash_password
from app.core.config import settings


SEED_USERS = [
    {
        "email": "coord@internado-uv.cl",
        "password": "coord123",
        "full_name": "Coordinador UV",
        "role": "coordinator",
    },
    {
        "email": "tutor@internado-uv.cl",
        "password": "tutor123",
        "full_name": "Tutor UV",
        "role": "tutor",
    },
    {
        "email": "estudiante@internado-uv.cl",
        "password": "estudiante123",
        "full_name": "Estudiante UV",
        "role": "student",
    },
]


def _looks_like_db_unavailable(exc: Exception) -> bool:
    text = str(exc)
    patterns = (
        "Connect call failed",
        "Connection refused",
        "could not connect",
        "connection is bad",
        "timeout expired",
    )
    return any(p in text for p in patterns)


def _start_local_db_if_possible() -> bool:
    repo_root = Path(__file__).resolve().parents[2]
    compose_file = repo_root / "docker-compose.yml"

    if not compose_file.exists():
        return False

    try:
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d", "db"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[seed] Base de datos Docker iniciada (servicio db).")
        return True
    except Exception:
        return False


async def seed() -> None:
    # Conectar a Keycloak
    try:
        # IMPORTANTE: Conectar al realm master primero para autenticación
        keycloak_admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_SERVER_URL,
            username=settings.KEYCLOAK_ADMIN_USERNAME,
            password=settings.KEYCLOAK_ADMIN_PASSWORD,
            realm_name=settings.KEYCLOAK_REALM,  # Realm donde se crearán los usuarios
            user_realm_name="master",  # Realm donde vive el usuario admin
            verify=True
        )
        print(f"[keycloak] Conectado a Keycloak (realm: {settings.KEYCLOAK_REALM})")
    except Exception as e:
        print(f"[keycloak] ⚠️  No se pudo conectar a Keycloak: {e}")
        print("[keycloak] Los usuarios se crearán solo en la base de datos local")
        keycloak_admin = None
    
    async with AsyncSessionLocal() as session:

        # ── Usuarios ──────────────────────────────────────────────────────
        users: dict[str, User] = {}
        for data in SEED_USERS:
            result = await session.execute(
                select(User).where(User.email == data["email"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"[skip]    {data['email']} ya existe en DB")
                users[data["role"]] = existing
            else:
                user = User(
                    email=data["email"],
                    hashed_password=hash_password(data["password"]),
                    full_name=data["full_name"],
                    role=data["role"],
                    has_completed_onboarding=True,  # Usuarios de seed ya completaron onboarding
                )
                session.add(user)
                await session.flush()
                users[data["role"]] = user
                print(f"[created] {data['email']} ({data['role']}) en DB")
            
            # Crear usuario en Keycloak
            if keycloak_admin:
                try:
                    # Verificar si el usuario ya existe en Keycloak
                    existing_users = keycloak_admin.get_users({"email": data["email"]})
                    
                    if existing_users:
                        keycloak_user_id = existing_users[0]["id"]
                        print(f"[skip]    {data['email']} ya existe en Keycloak")
                        
                        # Actualizar el ID del usuario en la BD si no coincide
                        if str(users[data["role"]].id) != keycloak_user_id:
                            users[data["role"]].id = keycloak_user_id
                            await session.flush()
                    else:
                        # Crear usuario en Keycloak
                        keycloak_user_id = keycloak_admin.create_user({
                            "email": data["email"],
                            "username": data["email"],
                            "enabled": True,
                            "emailVerified": True,
                            "firstName": data["full_name"].split()[0],
                            "lastName": " ".join(data["full_name"].split()[1:]) if len(data["full_name"].split()) > 1 else "",
                            "credentials": [{
                                "type": "password",
                                "value": data["password"],
                                "temporary": False
                            }]
                        })
                        print(f"[created] {data['email']} en Keycloak (ID: {keycloak_user_id})")
                        
                        # Asignar rol en Keycloak
                        role_obj = keycloak_admin.get_realm_role(data["role"])
                        keycloak_admin.assign_realm_roles(keycloak_user_id, [role_obj])
                        print(f"[assigned] rol '{data['role']}' a {data['email']} en Keycloak")
                        
                        # Actualizar el ID del usuario en la BD para que coincida con Keycloak
                        users[data["role"]].id = keycloak_user_id
                        await session.flush()
                        
                except KeycloakError as e:
                    print(f"[error]   Error creando {data['email']} en Keycloak: {e}")
                except Exception as e:
                    print(f"[error]   Error inesperado con {data['email']} en Keycloak: {e}")

        # ── Cohorte ───────────────────────────────────────────────────────
        result = await session.execute(
            select(Cohort).where(Cohort.name == "Internado 2026-1")
        )
        cohort = result.scalar_one_or_none()
        if cohort:
            print(f"[skip]    cohorte 'Internado 2026-1' ya existe")
        else:
            cohort = Cohort(
                name="Internado 2026-1",
                year=2026,
                semester=1,
                is_active=True,
            )
            session.add(cohort)
            await session.flush()
            print(f"[created] cohorte 'Internado 2026-1' ({cohort.id})")

        # ── Assignment ────────────────────────────────────────────────────
        # Vincula al estudiante con el tutor en el campo clínico
        student = users.get("student")
        tutor = users.get("tutor")

        if student and tutor and cohort:
            result = await session.execute(
                select(Assignment).where(
                    Assignment.student_id == student.id,
                    Assignment.cohort_id == cohort.id,
                    Assignment.is_active.is_(True),
                )
            )
            existing_assignment = result.scalar_one_or_none()
            if existing_assignment:
                print(f"[skip]    assignment estudiante→tutor ya existe")
            else:
                assignment = Assignment(
                    student_id=student.id,
                    tutor_id=tutor.id,
                    cohort_id=cohort.id,
                    clinical_site="Hospital Base Valdivia",
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 12, 31),
                    is_active=True,
                )
                session.add(assignment)
                print(f"[created] assignment: {student.full_name} → {tutor.full_name} @ Hospital Base Valdivia")

        await session.commit()
        print("\n✓ Seed completado")
        if cohort:
            print(f"  Cohorte ID: {cohort.id}")
        if student:
            print(f"  Estudiante ID: {student.id}")


async def seed_with_recovery() -> None:
    try:
        await seed()
    except Exception as exc:
        if not _looks_like_db_unavailable(exc):
            raise

        print("[seed] No se pudo conectar a PostgreSQL. Intentando iniciar db...")
        if not _start_local_db_if_possible():
            raise

        # Dar un margen breve para que Postgres acepte conexiones.
        await asyncio.sleep(2)
        await seed()


if __name__ == "__main__":
    asyncio.run(seed_with_recovery())
