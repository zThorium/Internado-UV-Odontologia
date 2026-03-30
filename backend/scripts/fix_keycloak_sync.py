"""
Script automatizado para sincronizar usuarios con Keycloak.

Este script:
1. Limpia usuarios no coordinadores de la BD
2. Crea usuarios en Keycloak y BD con IDs sincronizados
3. Crea una asignación de ejemplo
"""
import asyncio
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.cohort import Cohort
from app.models.assignment import Assignment
from app.core.keycloak_client import (
    create_keycloak_user,
    assign_role_to_keycloak_user,
    is_keycloak_available,
)
from app.core.security import hash_password
from uuid import UUID


async def fix_sync():
    """Proceso completo de sincronización."""
    
    print("=" * 70)
    print("🔧 FIX AUTOMÁTICO: Sincronización Keycloak")
    print("=" * 70)
    
    # Verificar Keycloak
    print("\n1️⃣ Verificando Keycloak...")
    if not is_keycloak_available():
        print("❌ Keycloak no está disponible")
        print("   Asegúrate de que esté corriendo: ./dev.sh")
        return
    print("✅ Keycloak disponible")
    
    async with AsyncSessionLocal() as session:
        # Paso 1: Limpiar usuarios no coordinadores
        print("\n2️⃣ Limpiando usuarios no coordinadores...")
        try:
            await session.execute(text("DELETE FROM evaluation_items"))
            await session.execute(text("DELETE FROM evaluations"))
            await session.execute(text("DELETE FROM logbook_procedures"))
            await session.execute(text("DELETE FROM logbook_entries"))
            await session.execute(text("DELETE FROM incidents"))
            await session.execute(text("DELETE FROM assignments"))
            
            result = await session.execute(
                text("DELETE FROM users WHERE role != 'coordinator' RETURNING email")
            )
            deleted = result.fetchall()
            await session.commit()
            
            if deleted:
                print(f"✅ Eliminados {len(deleted)} usuarios")
            else:
                print("✅ No había usuarios para eliminar")
                
        except Exception as e:
            print(f"❌ Error limpiando: {e}")
            await session.rollback()
            return
        
        # Paso 2: Obtener o crear cohorte
        print("\n3️⃣ Verificando cohorte...")
        result = await session.execute(
            select(Cohort).where(Cohort.name == "Internado 2026-1")
        )
        cohort = result.scalar_one_or_none()
        
        if not cohort:
            cohort = Cohort(
                name="Internado 2026-1",
                year=2026,
                semester=1,
                is_active=True,
            )
            session.add(cohort)
            await session.flush()
            print(f"✅ Cohorte creado: {cohort.name}")
        else:
            print(f"✅ Cohorte existe: {cohort.name}")
        
        # Paso 3: Crear usuarios con IDs sincronizados
        print("\n4️⃣ Creando usuarios con IDs sincronizados...")
        
        users_to_create = [
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
        
        created_users = {}
        
        for user_data in users_to_create:
            try:
                print(f"\n   📝 Creando {user_data['email']}...")
                
                # Verificar si ya existe en BD
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                if result.scalar_one_or_none():
                    print(f"   ⚠️  Ya existe en BD, omitiendo...")
                    continue
                
                # Crear en Keycloak
                names = user_data["full_name"].split(" ", 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ""
                
                keycloak_user_id = create_keycloak_user(
                    email=user_data["email"],
                    password=user_data["password"],
                    first_name=first_name,
                    last_name=last_name,
                )
                print(f"   ✓ Creado en Keycloak (ID: {keycloak_user_id[:8]}...)")
                
                # Asignar rol en Keycloak
                assign_role_to_keycloak_user(keycloak_user_id, user_data["role"])
                print(f"   ✓ Rol asignado: {user_data['role']}")
                
                # Crear en BD con el mismo ID de Keycloak
                new_user = User(
                    id=UUID(keycloak_user_id),
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=True,
                    has_completed_onboarding=False,
                )
                session.add(new_user)
                await session.flush()
                
                created_users[user_data["role"]] = new_user
                print(f"   ✅ {user_data['email']} creado (ID sincronizado)")
                
            except ValueError as e:
                if "ya existe" in str(e).lower():
                    print(f"   ⚠️  Ya existe en Keycloak, omitiendo...")
                else:
                    print(f"   ❌ Error: {e}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                await session.rollback()
                return
        
        # Paso 4: Crear asignación
        if "tutor" in created_users and "student" in created_users:
            print("\n5️⃣ Creando asignación tutor-estudiante...")
            try:
                assignment = Assignment(
                    student_id=created_users["student"].id,
                    tutor_id=created_users["tutor"].id,
                    cohort_id=cohort.id,
                    clinical_site="Hospital Base Valdivia",
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 12, 31),
                    is_active=True,
                )
                session.add(assignment)
                print("✅ Asignación creada")
            except Exception as e:
                print(f"❌ Error creando asignación: {e}")
        
        # Commit final
        try:
            await session.commit()
            print("\n" + "=" * 70)
            print("✅ PROCESO COMPLETADO")
            print("=" * 70)
            print("\n📋 Credenciales:")
            print("   Coordinador: coord@internado-uv.cl / coord123")
            print("   Tutor:       tutor@internado-uv.cl / tutor123")
            print("   Estudiante:  estudiante@internado-uv.cl / estudiante123")
            print("\n💡 Ahora puedes:")
            print("   1. Login como tutor → Ver estudiantes asignados")
            print("   2. Login como estudiante → Ver tu tutor")
            print("   3. El tour de bienvenida ya no se repetirá")
            print()
        except Exception as e:
            print(f"\n❌ Error en commit final: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(fix_sync())
