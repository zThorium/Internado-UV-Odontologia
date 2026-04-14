"""
Script para configurar Keycloak desde cero.

Crea:
- Realm: internado-uv
- Roles: student, tutor, coordinator
- Cliente: internado-backend
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from app.core.config import settings


def setup_keycloak():
    """Configura Keycloak desde cero."""
    
    print("=" * 70)
    print("🔧 CONFIGURACIÓN DE KEYCLOAK")
    print("=" * 70)
    
    try:
        # Conectar como admin al realm master
        print("\n1️⃣ Conectando a Keycloak...")
        admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_SERVER_URL,
            username=settings.KEYCLOAK_ADMIN_USERNAME,
            password=settings.KEYCLOAK_ADMIN_PASSWORD,
            realm_name="master",
            verify=True
        )
        print("✅ Conectado a Keycloak")
        
        # Crear realm
        print(f"\n2️⃣ Creando realm '{settings.KEYCLOAK_REALM}'...")
        try:
            admin.create_realm(
                payload={
                    "realm": settings.KEYCLOAK_REALM,
                    "enabled": True,
                    "displayName": "Internado Odontología UV",
                    "registrationAllowed": False,
                    "resetPasswordAllowed": True,
                    "rememberMe": True,
                    "verifyEmail": False,
                    "loginWithEmailAllowed": True,
                    "duplicateEmailsAllowed": False,
                    "sslRequired": "none",
                    "accessTokenLifespan": 300,  # 5 minutos
                    "accessTokenLifespanForImplicitFlow": 900,
                    "ssoSessionIdleTimeout": 1800,  # 30 minutos
                    "ssoSessionMaxLifespan": 36000,  # 10 horas
                    "offlineSessionIdleTimeout": 2592000,
                    "accessCodeLifespan": 60,
                    "accessCodeLifespanUserAction": 300,
                    "accessCodeLifespanLogin": 1800,
                },
                skip_exists=True
            )
            print(f"✅ Realm '{settings.KEYCLOAK_REALM}' creado")
        except KeycloakError as e:
            if "409" in str(e):
                print(f"⚠️  Realm '{settings.KEYCLOAK_REALM}' ya existe")
            else:
                raise
        
        # Cambiar al nuevo realm - IMPORTANTE: Reconectar con el realm correcto
        admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_SERVER_URL,
            username=settings.KEYCLOAK_ADMIN_USERNAME,
            password=settings.KEYCLOAK_ADMIN_PASSWORD,
            realm_name=settings.KEYCLOAK_REALM,
            user_realm_name="master",
            verify=True
        )
        
        # Crear roles
        print("\n3️⃣ Creando roles...")
        roles = ["student", "tutor", "coordinator"]
        for role in roles:
            try:
                # Verificar si el rol ya existe
                existing_roles = admin.get_realm_roles()
                role_exists = any(r["name"] == role for r in existing_roles)
                
                if not role_exists:
                    admin.create_realm_role(
                        payload={
                            "name": role,
                            "description": f"Rol de {role}",
                        }
                    )
                    print(f"   ✓ Rol '{role}' creado")
                else:
                    print(f"   ⚠️  Rol '{role}' ya existe")
            except Exception as e:
                print(f"   ❌ Error creando rol '{role}': {e}")
        
        # Crear cliente backend
        print(f"\n4️⃣ Creando cliente '{settings.KEYCLOAK_CLIENT_ID}'...")
        try:
            # Verificar si el cliente ya existe
            clients = admin.get_clients()
            existing_client = next((c for c in clients if c['clientId'] == settings.KEYCLOAK_CLIENT_ID), None)
            
            if existing_client:
                print(f"⚠️  Cliente '{settings.KEYCLOAK_CLIENT_ID}' ya existe")
                client_id = existing_client['id']
            else:
                client_id = admin.create_client(
                    payload={
                        "clientId": settings.KEYCLOAK_CLIENT_ID,
                        "enabled": True,
                        "publicClient": False,
                        "directAccessGrantsEnabled": True,  # Password Grant
                        "serviceAccountsEnabled": True,
                        "authorizationServicesEnabled": False,
                        "standardFlowEnabled": True,  # Authorization Code
                        "implicitFlowEnabled": False,
                        "redirectUris": [
                            settings.KEYCLOAK_REDIRECT_URI,
                            "http://localhost:5173/*",
                        ],
                        "webOrigins": [
                            "http://localhost:5173",
                            "http://localhost:8000",
                        ],
                        "protocol": "openid-connect",
                    },
                    skip_exists=True
                )
                print(f"✅ Cliente '{settings.KEYCLOAK_CLIENT_ID}' creado")
            
            # Obtener el secret del cliente (siempre, para actualizar el .env)
            client_secret = admin.get_client_secrets(client_id)
            print(f"\n📋 Client Secret: {client_secret['value']}")
            print(f"   Actualiza este valor en backend/.env:")
            print(f"   KEYCLOAK_CLIENT_SECRET={client_secret['value']}")
            
        except KeycloakError as e:
            if "409" in str(e):
                print(f"⚠️  Cliente '{settings.KEYCLOAK_CLIENT_ID}' ya existe")
            else:
                raise
        
        # Crear cliente frontend (público)
        print(f"\n5️⃣ Creando cliente 'internado-frontend'...")
        try:
            # Verificar si el cliente ya existe
            clients = admin.get_clients()
            existing_frontend = next((c for c in clients if c['clientId'] == 'internado-frontend'), None)
            
            if existing_frontend:
                print(f"⚠️  Cliente 'internado-frontend' ya existe")
            else:
                frontend_client_id = admin.create_client(
                    payload={
                        "clientId": "internado-frontend",
                        "enabled": True,
                        "publicClient": True,  # Cliente público (SPA)
                        "directAccessGrantsEnabled": False,
                        "serviceAccountsEnabled": False,
                        "authorizationServicesEnabled": False,
                        "standardFlowEnabled": True,  # Authorization Code
                        "implicitFlowEnabled": False,
                        "redirectUris": [
                            "http://localhost:5173/*",
                            "http://localhost:5173",
                        ],
                        "webOrigins": [
                            "http://localhost:5173",
                            "http://localhost:8000",
                            "+",  # Permite todos los orígenes de redirectUris
                        ],
                        "protocol": "openid-connect",
                        "attributes": {
                            "pkce.code.challenge.method": "S256",  # PKCE para seguridad
                        },
                    },
                    skip_exists=True
                )
                print(f"✅ Cliente 'internado-frontend' creado")
            
        except KeycloakError as e:
            if "409" in str(e):
                print(f"⚠️  Cliente 'internado-frontend' ya existe")
            else:
                raise
        
        print("\n" + "=" * 70)
        print("✅ KEYCLOAK CONFIGURADO CORRECTAMENTE")
        print("=" * 70)
        print(f"\n🌐 Keycloak Admin: {settings.KEYCLOAK_SERVER_URL}/admin")
        print(f"   Usuario: {settings.KEYCLOAK_ADMIN_USERNAME}")
        print(f"   Password: {settings.KEYCLOAK_ADMIN_PASSWORD}")
        print(f"   Realm: {settings.KEYCLOAK_REALM}")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error configurando Keycloak: {e}")
        print("\n💡 Asegúrate de que:")
        print("   1. Keycloak esté corriendo (./dev.sh)")
        print("   2. Las credenciales de admin sean correctas")
        return False


if __name__ == "__main__":
    # Esperar un poco para que Keycloak esté listo
    print("⏳ Esperando a que Keycloak esté listo...")
    time.sleep(2)
    
    success = setup_keycloak()
    sys.exit(0 if success else 1)
