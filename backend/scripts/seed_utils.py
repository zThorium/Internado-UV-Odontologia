"""Utilidades compartidas para scripts de seed y alta de usuarios."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User

UserRole = Literal["student", "tutor", "coordinator"]


@dataclass
class SeedUserSpec:
    email: str
    password: str
    full_name: str
    role: UserRole


def connect_keycloak_admin() -> KeycloakAdmin | None:
    try:
        admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_SERVER_URL,
            username=settings.KEYCLOAK_ADMIN_USERNAME,
            password=settings.KEYCLOAK_ADMIN_PASSWORD,
            realm_name=settings.KEYCLOAK_REALM,
            user_realm_name="master",
            verify=True,
        )
        print(f"[keycloak] Conectado (realm: {settings.KEYCLOAK_REALM})")
        return admin
    except Exception as exc:
        print(f"[keycloak] No se pudo conectar: {exc}")
        print("[keycloak] El usuario se creará solo en la base de datos")
        return None


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split()
    if not parts:
        return full_name, ""
    return parts[0], " ".join(parts[1:])


async def _sync_keycloak_user(
    keycloak_admin: KeycloakAdmin,
    session: AsyncSession,
    user: User,
    spec: SeedUserSpec,
) -> None:
    try:
        existing_users = keycloak_admin.get_users({"email": spec.email})
        if existing_users:
            keycloak_user_id = existing_users[0]["id"]
            print(f"[skip]    {spec.email} ya existe en Keycloak")
            if str(user.id) != keycloak_user_id:
                user.id = uuid.UUID(keycloak_user_id)
                await session.flush()
            return

        keycloak_user_id = keycloak_admin.create_user(
            {
                "email": spec.email,
                "username": spec.email,
                "enabled": True,
                "emailVerified": True,
                "firstName": _split_name(spec.full_name)[0],
                "lastName": _split_name(spec.full_name)[1],
                "credentials": [
                    {
                        "type": "password",
                        "value": spec.password,
                        "temporary": False,
                    }
                ],
            }
        )
        print(f"[created] {spec.email} en Keycloak (ID: {keycloak_user_id})")

        role_obj = keycloak_admin.get_realm_role(spec.role)
        keycloak_admin.assign_realm_roles(keycloak_user_id, [role_obj])
        print(f"[assigned] rol '{spec.role}' a {spec.email} en Keycloak")

        user.id = uuid.UUID(keycloak_user_id)
        await session.flush()
    except KeycloakError as exc:
        print(f"[error]   Keycloak {spec.email}: {exc}")
    except Exception as exc:
        print(f"[error]   Keycloak inesperado {spec.email}: {exc}")


async def ensure_user_in_db_and_keycloak(
    session: AsyncSession,
    keycloak_admin: KeycloakAdmin | None,
    spec: SeedUserSpec,
    *,
    mark_onboarding_complete: bool = True,
) -> User:
    result = await session.execute(select(User).where(User.email == spec.email))
    user = result.scalar_one_or_none()

    if user:
        print(f"[skip]    {spec.email} ya existe en DB")
    else:
        user = User(
            email=spec.email,
            hashed_password=hash_password(spec.password),
            full_name=spec.full_name,
            role=spec.role,
            has_completed_onboarding=mark_onboarding_complete,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        print(f"[created] {spec.email} ({spec.role}) en DB")

    if keycloak_admin is not None:
        await _sync_keycloak_user(keycloak_admin, session, user, spec)

    return user
