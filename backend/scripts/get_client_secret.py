"""Script para obtener el client secret de internado-backend"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
from app.core.config import settings

admin = KeycloakAdmin(
    server_url=settings.KEYCLOAK_SERVER_URL,
    username=settings.KEYCLOAK_ADMIN_USERNAME,
    password=settings.KEYCLOAK_ADMIN_PASSWORD,
    realm_name=settings.KEYCLOAK_REALM,
    user_realm_name='master',
    verify=True
)

clients = admin.get_clients()
for client in clients:
    if client['clientId'] == 'internado-backend':
        client_id = client['id']
        secret = admin.get_client_secrets(client_id)
        print(secret['value'])
        break
