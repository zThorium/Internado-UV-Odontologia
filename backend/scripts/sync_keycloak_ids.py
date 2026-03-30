"""
Script para sincronizar IDs de usuarios entre la base de datos local y Keycloak.

Este script actualiza los IDs de los usuarios en la base de datos local para que coincidan
con sus IDs en Keycloak, lo cual es necesario para que las asignaciones funcionen correctamente.

ADVERTENCIA: Este script modifica directamente los IDs en la base de datos.
Asegúrate de hacer un backup antes de ejecutarlo.
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.keycloak_client import get_keycloak_admin


async def sync_user_ids():
    """Sincroniza los IDs de usuarios entre BD local y Keycloak."""
    print("🔄 Iniciando sincronización de IDs de usuarios...")
    
    async with AsyncSessionLocal() as session:
        # Obtener todos los usuarios de la BD local
        result = await session.execute(select(User))
        local_users = result.scalars().all()
        
        if not local_users:
            print("✓ No hay usuarios en la base de datos local")
            return
        
        # Obtener admin de Keycloak
        try:
            admin = get_keycloak_admin()
        except Exception as e:
            print(f"❌ Error conectando con Keycloak: {e}")
            print("   Asegúrate de que Keycloak esté corriendo")
            return
        
        updates = []
        
        for user in local_users:
            try:
                # Buscar usuario en Keycloak por email
                keycloak_users = admin.get_users({"email": user.email, "exact": True})
                
                if not keycloak_users:
                    print(f"⚠️  Usuario {user.email} no encontrado en Keycloak")
                    continue
                
                keycloak_user = keycloak_users[0]
                keycloak_id = keycloak_user["id"]
                
                if str(user.id) == keycloak_id:
                    print(f"✓ {user.email}: IDs ya sincronizados")
                else:
                    print(f"🔄 {user.email}:")
                    print(f"   BD local: {user.id}")
                    print(f"   Keycloak: {keycloak_id}")
                    updates.append({
                        "old_id": str(user.id),
                        "new_id": keycloak_id,
                        "email": user.email,
                        "role": user.role
                    })
            
            except Exception as e:
                print(f"❌ Error procesando {user.email}: {e}")
        
        if not updates:
            print("\n✓ Todos los IDs ya están sincronizados")
            return
        
        print(f"\n📋 Se encontraron {len(updates)} usuarios que necesitan actualización")
        print("\n⚠️  ADVERTENCIA: Esta operación modificará los IDs en la base de datos")
        print("   Asegúrate de tener un backup antes de continuar")
        
        response = input("\n¿Deseas continuar? (si/no): ")
        if response.lower() not in ["si", "sí", "s", "yes", "y"]:
            print("❌ Operación cancelada")
            return
        
        print("\n🔄 Actualizando IDs...")
        
        # Primero, actualizar todas las referencias en las tablas relacionadas
        for update in updates:
            try:
                print(f"🔄 Actualizando referencias de {update['email']}...")
                
                # Assignments
                await session.execute(
                    text("UPDATE assignments SET student_id = :new_id WHERE student_id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                await session.execute(
                    text("UPDATE assignments SET tutor_id = :new_id WHERE tutor_id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                
                # Evaluations
                await session.execute(
                    text("UPDATE evaluations SET student_id = :new_id WHERE student_id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                await session.execute(
                    text("UPDATE evaluations SET tutor_id = :new_id WHERE tutor_id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                
                # Logbook entries
                await session.execute(
                    text("UPDATE logbook_entries SET student_id = :new_id WHERE student_id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                
                # Incidents
                await session.execute(
                    text("UPDATE incidents SET student_id = :new_id WHERE student_id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                
                print(f"  ✓ Referencias actualizadas")
                
            except Exception as e:
                print(f"❌ Error actualizando referencias de {update['email']}: {e}")
                await session.rollback()
                return
        
        # Ahora actualizar los IDs de los usuarios
        print("\n🔄 Actualizando IDs de usuarios...")
        for update in updates:
            try:
                await session.execute(
                    text("UPDATE users SET id = :new_id WHERE id = :old_id"),
                    {"new_id": update["new_id"], "old_id": update["old_id"]}
                )
                print(f"✓ {update['email']}: ID actualizado")
                
            except Exception as e:
                print(f"❌ Error actualizando {update['email']}: {e}")
                await session.rollback()
                return
        
        await session.commit()
        print(f"\n✅ Sincronización completada: {len(updates)} usuarios actualizados")


if __name__ == "__main__":
    asyncio.run(sync_user_ids())
