"""
Script para crear el usuario coordinador inicial en producción.

Ejecutar desde el directorio backend/:
    python -m scripts.create_coordinator

Las credenciales se leen de variables de entorno:
    COORDINATOR_EMAIL    (default: coord@internado-uv.cl)
    COORDINATOR_PASSWORD (default: CAMBIAR_EN_PRODUCCION)
    COORDINATOR_NAME     (default: Coordinador UV)
"""

import asyncio
import os

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


async def create_coordinator() -> None:
    email = os.getenv("COORDINATOR_EMAIL", "coord@internado-uv.cl")
    password = os.getenv("COORDINATOR_PASSWORD", "CAMBIAR_EN_PRODUCCION")
    full_name = os.getenv("COORDINATOR_NAME", "Coordinador UV")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[skip] El coordinador {email} ya existe.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role="coordinator",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"[created] Coordinador creado: {email}")


if __name__ == "__main__":
    asyncio.run(create_coordinator())
