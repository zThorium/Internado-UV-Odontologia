"""
Script para obtener el client secret de Keycloak y crear el archivo .env
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
from app.core.config import settings


def get_client_secret_and_setup_env():
    """Obtiene el client secret y crea el archivo .env"""
    
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
        
        # Obtener el secret
        client_secret = admin.get_client_secrets(client_id)
        secret_value = client_secret['value']
        
        print(f"✅ Client Secret obtenido: {secret_value}")
        
        # Crear archivo .env
        env_file = Path(__file__).parent.parent / '.env'
        env_example = Path(__file__).parent.parent / '.env.example'
        
        if env_file.exists():
            print(f"⚠️  El archivo .env ya existe")
            # Leer el archivo actual
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Actualizar el secret
            if 'KEYCLOAK_CLIENT_SECRET=' in content:
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('KEYCLOAK_CLIENT_SECRET='):
                        new_lines.append(f'KEYCLOAK_CLIENT_SECRET={secret_value}')
                    else:
                        new_lines.append(line)
                content = '\n'.join(new_lines)
            else:
                # Agregar el secret
                content += f'\nKEYCLOAK_CLIENT_SECRET={secret_value}\n'
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Archivo .env actualizado con el nuevo secret")
        else:
            # Copiar desde .env.example y actualizar el secret
            with open(env_example, 'r') as f:
                content = f.read()
            
            # Reemplazar el secret placeholder
            content = content.replace(
                'KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret',
                f'KEYCLOAK_CLIENT_SECRET={secret_value}'
            )
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Archivo .env creado con el client secret")
        
        print(f"\n📝 Archivo .env ubicado en: {env_file}")
        print(f"   KEYCLOAK_CLIENT_SECRET={secret_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = get_client_secret_and_setup_env()
    sys.exit(0 if success else 1)
