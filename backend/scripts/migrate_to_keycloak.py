"""
Script de migración de usuarios de PostgreSQL a Keycloak.

Este script migra todos los usuarios existentes en la base de datos
a Keycloak, preservando sus roles y configurando credenciales temporales.

Uso:
    cd backend
    python -m scripts.migrate_to_keycloak

Prerrequisitos:
    - Keycloak debe estar corriendo en http://localhost:8080
    - El realm 'internado-uv' debe estar creado
    - Los roles 'student', 'tutor', 'coordinator' deben existir
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

from app.models.user import User
from app.core.config import settings


# Configurar cliente admin de Keycloak
keycloak_admin = KeycloakAdmin(
    server_url=settings.KEYCLOAK_SERVER_URL,
    username="admin",
    password="admin123",
    realm_name=settings.KEYCLOAK_REALM,
    user_realm_name="master",  # El usuario admin vive en master
    verify=True
)


async def get_all_users(db: AsyncSession):
    """Obtiene todos los usuarios de PostgreSQL"""
    result = await db.execute(select(User))
    return result.scalars().all()


def create_keycloak_user(user: User):
    """
    Crea un usuario en Keycloak.

    Args:
        user: Modelo User de SQLAlchemy

    Returns:
        user_id de Keycloak si se creó exitosamente, None en caso contrario
    """
    try:
        # Separar nombre completo en firstName y lastName
        name_parts = user.full_name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else user.full_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Crear payload de usuario
        user_payload = {
            "email": user.email,
            "username": user.email,  # Usar email como username
            "enabled": user.is_active,
            "emailVerified": True,
            "firstName": first_name,
            "lastName": last_name,
            "credentials": [{
                "type": "password",
                "value": "changeme123",  # Contraseña temporal
                "temporary": True  # Forzar cambio en primer login
            }],
            "attributes": {
                "postgres_user_id": [str(user.id)],  # Guardar ID original
                "has_completed_onboarding": [str(user.has_completed_onboarding).lower()]
            }
        }

        # Verificar si el usuario ya existe
        existing_users = keycloak_admin.get_users({"email": user.email})
        if existing_users:
            print(f"  ⚠️  Usuario {user.email} ya existe en Keycloak, omitiendo...")
            return existing_users[0]["id"]

        # Crear usuario en Keycloak
        user_id = keycloak_admin.create_user(user_payload)
        print(f"  ✅ Usuario creado: {user.email} (ID: {user_id})")

        return user_id

    except KeycloakError as e:
        print(f"  ❌ Error creando usuario {user.email}: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error inesperado con {user.email}: {e}")
        return None


def assign_role_to_user(user_id: str, role_name: str):
    """
    Asigna un rol de realm a un usuario en Keycloak.

    Args:
        user_id: ID del usuario en Keycloak
        role_name: Nombre del rol (student, tutor, coordinator)
    """
    try:
        # Obtener el rol por nombre
        role = keycloak_admin.get_realm_role(role_name)

        if not role:
            print(f"  ⚠️  Rol '{role_name}' no existe en Keycloak")
            return False

        # Asignar rol al usuario
        keycloak_admin.assign_realm_roles(user_id, [role])
        print(f"  ✅ Rol '{role_name}' asignado correctamente")
        return True

    except KeycloakError as e:
        print(f"  ❌ Error asignando rol '{role_name}': {e}")
        return False


async def migrate_users():
    """Función principal de migración"""
    print("=" * 60)
    print("MIGRACIÓN DE USUARIOS A KEYCLOAK")
    print("=" * 60)
    print()

    # Verificar conexión con Keycloak
    print("1. Verificando conexión con Keycloak...")
    try:
        keycloak_admin.get_realm(settings.KEYCLOAK_REALM)
        print(f"   ✅ Conectado a Keycloak (realm: {settings.KEYCLOAK_REALM})")
    except Exception as e:
        print(f"   ❌ Error conectando a Keycloak: {e}")
        print(f"   💡 Verifica que Keycloak esté corriendo en {settings.KEYCLOAK_SERVER_URL}")
        return
    print()

    # Verificar que los roles existan
    print("2. Verificando roles en Keycloak...")
    required_roles = ["student", "tutor", "coordinator"]
    for role_name in required_roles:
        try:
            role = keycloak_admin.get_realm_role(role_name)
            if role:
                print(f"   ✅ Rol '{role_name}' existe")
            else:
                print(f"   ⚠️  Rol '{role_name}' NO existe. Créalo manualmente en Keycloak.")
        except KeycloakError:
            print(f"   ⚠️  Rol '{role_name}' NO existe. Créalo manualmente en Keycloak.")
    print()

    # Conectar a PostgreSQL
    print("3. Conectando a PostgreSQL...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        users = await get_all_users(db)
        print(f"   ✅ Encontrados {len(users)} usuarios en PostgreSQL")
        print()

        # Migrar cada usuario
        print("4. Migrando usuarios...")
        migrated_count = 0
        failed_count = 0

        for idx, user in enumerate(users, 1):
            print(f"\n[{idx}/{len(users)}] Migrando: {user.email} ({user.role})")

            # Crear usuario en Keycloak
            keycloak_user_id = create_keycloak_user(user)

            if keycloak_user_id:
                # Asignar rol
                if assign_role_to_user(keycloak_user_id, user.role):
                    migrated_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1

    await engine.dispose()

    # Resumen
    print()
    print("=" * 60)
    print("RESUMEN DE MIGRACIÓN")
    print("=" * 60)
    print(f"Total de usuarios:     {len(users)}")
    print(f"✅ Migrados:           {migrated_count}")
    print(f"❌ Fallidos:           {failed_count}")
    print()
    print("📝 IMPORTANTE:")
    print("   - Contraseña temporal para todos: changeme123")
    print("   - Los usuarios deberán cambiarla en su primer login")
    print("   - Los IDs originales se guardaron en attributes.postgres_user_id")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    print()
    print("⚠️  ADVERTENCIA:")
    print("   Este script creará usuarios en Keycloak.")
    print("   Asegúrate de que:")
    print("   1. Keycloak esté corriendo (http://localhost:8080)")
    print("   2. El realm 'internado-uv' esté creado")
    print("   3. Los roles student, tutor, coordinator existan")
    print()

    # Permitir --yes para ejecución no interactiva
    if "--yes" in sys.argv or "-y" in sys.argv:
        asyncio.run(migrate_users())
    else:
        response = input("¿Deseas continuar? (si/no): ")
        if response.lower() in ["si", "s", "yes", "y"]:
            asyncio.run(migrate_users())
        else:
            print("Migración cancelada.")
