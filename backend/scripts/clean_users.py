"""
Script para limpiar usuarios no coordinadores de la base de datos.
Útil después de recrear Keycloak desde cero.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def clean_users():
    """Elimina todos los usuarios excepto coordinadores."""
    print("🧹 Limpiando usuarios no coordinadores...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Eliminar datos relacionados primero
            await session.execute(text("DELETE FROM evaluation_items"))
            await session.execute(text("DELETE FROM evaluations"))
            await session.execute(text("DELETE FROM logbook_procedures"))
            await session.execute(text("DELETE FROM logbook_entries"))
            await session.execute(text("DELETE FROM incidents"))
            await session.execute(text("DELETE FROM assignments"))
            
            # Eliminar usuarios no coordinadores
            result = await session.execute(
                text("DELETE FROM users WHERE role != 'coordinator' RETURNING email")
            )
            deleted = result.fetchall()
            
            await session.commit()
            
            if deleted:
                print(f"\n✅ Eliminados {len(deleted)} usuarios:")
                for row in deleted:
                    print(f"   - {row[0]}")
            else:
                print("\n✓ No había usuarios para eliminar")
            
            print("\n💡 Ahora puedes recrear los usuarios desde el coordinador")
            print("   Los nuevos usuarios tendrán IDs sincronizados con Keycloak")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(clean_users())
