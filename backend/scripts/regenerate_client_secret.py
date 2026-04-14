"""
Script para regenerar el client secret del cliente backend.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
from app.core.config import settings


def regenerate_client_secret():
    """Regenera el client secret del cliente backend."""
    
    try:
        # Conectar como admin
        admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_SERVER_URL,
            username=settings.KEYCLOAK_ADMIN_USERNAME,
            password=settings.KEYCLOAK_ADMIN_PASSWORD,
            realm_name="master",
            verify=True
        )
        admin.realm_name = settings.KEYCLOAK_REALM
        
        # Buscar el cliente backend
        clients = admin.get_clients()
        backend_client = next((c for c in clients if c['clientId'] == settings.KEYCLOAK_CLIENT_ID), None)
        
        if not backend_client:
            print(f"❌ Cliente '{settings.KEYCLOAK_CLIENT_ID}' no encontrado")
            return False
        
        client_id = backend_client['id']
        
        print(f"Cliente encontrado: {backend_client['clientId']}")
        print(f"  ID: {client_id}")
        print(f"  publicClient: {backend_client.get('publicClient')}")
        print(f"  directAccessGrantsEnabled: {backend_client.get('directAccessGrantsEnabled')}")
        
        # Regenerar el secret
        print("\nRegenerando client secret...")
        new_secret = admin.generate_client_secrets(client_id)
        
        print(f"\n✅ Nuevo client secret generado: {new_secret['value']}")
        print(f"\nActualiza este valor en backend/.env:")
        print(f"KEYCLOAK_CLIENT_SECRET={new_secret['value']}")
        
        # Actualizar el archivo .env
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Actualizar el secret
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('KEYCLOAK_CLIENT_SECRET='):
                    new_lines.append(f'KEYCLOAK_CLIENT_SECRET={new_secret["value"]}')
                else:
                    new_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.write('\n'.join(new_lines))
            
            print(f"\n✅ Archivo .env actualizado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = regenerate_client_secret()
    sys.exit(0 if success else 1)
