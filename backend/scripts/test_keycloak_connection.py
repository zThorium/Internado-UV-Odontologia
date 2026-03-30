"""
Script de diagnóstico para verificar la conexión con Keycloak.

Uso:
    cd backend
    python -m scripts.test_keycloak_connection
"""

import sys
import requests
from app.core.config import settings

def test_keycloak_connection():
    """Verifica la conexión con Keycloak y la configuración."""
    
    print("=" * 70)
    print("DIAGNÓSTICO DE CONEXIÓN CON KEYCLOAK")
    print("=" * 70)
    print()
    
    # 1. Verificar configuración
    print("1. Configuración actual:")
    print(f"   KEYCLOAK_SERVER_URL: {settings.KEYCLOAK_SERVER_URL}")
    print(f"   KEYCLOAK_REALM: {settings.KEYCLOAK_REALM}")
    print(f"   KEYCLOAK_CLIENT_ID: {settings.KEYCLOAK_CLIENT_ID}")
    print(f"   KEYCLOAK_ADMIN_USERNAME: {settings.KEYCLOAK_ADMIN_USERNAME}")
    print(f"   KEYCLOAK_ADMIN_CLIENT_ID: {settings.KEYCLOAK_ADMIN_CLIENT_ID}")
    print()
    
    # 2. Verificar que Keycloak está corriendo
    print("2. Verificando que Keycloak está corriendo...")
    try:
        response = requests.get(f"{settings.KEYCLOAK_SERVER_URL}/realms/master/.well-known/openid-configuration", timeout=5)
        if response.status_code == 200:
            print("   ✅ Keycloak está corriendo")
        else:
            print(f"   ❌ Keycloak respondió con código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ No se puede conectar a {settings.KEYCLOAK_SERVER_URL}")
        print("   💡 Verifica que Keycloak esté corriendo: docker ps | grep keycloak")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 3. Verificar realm de la aplicación
    print(f"3. Verificando realm '{settings.KEYCLOAK_REALM}'...")
    try:
        response = requests.get(f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/.well-known/openid-configuration", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Realm '{settings.KEYCLOAK_REALM}' existe")
        else:
            print(f"   ❌ Realm '{settings.KEYCLOAK_REALM}' no existe")
            print("   💡 Crea el realm en Keycloak Admin Console")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 4. Verificar autenticación de admin
    print("4. Verificando autenticación de admin...")
    try:
        # Autenticar contra realm master
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
        response = requests.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,
                "username": settings.KEYCLOAK_ADMIN_USERNAME,
                "password": settings.KEYCLOAK_ADMIN_PASSWORD,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            admin_token = token_data.get("access_token")
            print("   ✅ Autenticación de admin exitosa")
            print(f"   Token obtenido (primeros 20 chars): {admin_token[:20]}...")
        else:
            print(f"   ❌ Error de autenticación: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            print("   💡 Verifica KEYCLOAK_ADMIN_USERNAME y KEYCLOAK_ADMIN_PASSWORD en .env")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 5. Verificar roles en el realm
    print(f"5. Verificando roles en realm '{settings.KEYCLOAK_REALM}'...")
    try:
        roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/roles"
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(roles_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            roles = response.json()
            role_names = [r["name"] for r in roles]
            
            required_roles = ["student", "tutor", "coordinator"]
            for role_name in required_roles:
                if role_name in role_names:
                    print(f"   ✅ Rol '{role_name}' existe")
                else:
                    print(f"   ⚠️  Rol '{role_name}' NO existe")
                    print(f"   💡 Crea el rol en Keycloak Admin Console o ejecuta el script de migración")
        else:
            print(f"   ❌ Error obteniendo roles: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 6. Probar creación de usuario de prueba
    print("6. Probando creación de usuario de prueba...")
    test_email = "test-diagnostico@uv.cl"
    try:
        users_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # Verificar si ya existe
        check_response = requests.get(f"{users_url}?email={test_email}", headers=headers, timeout=10)
        if check_response.json():
            print(f"   ⚠️  Usuario de prueba {test_email} ya existe (esto es normal)")
            print("   💡 Puedes eliminarlo manualmente desde Keycloak Admin Console")
        else:
            # Intentar crear
            user_data = {
                "email": test_email,
                "username": test_email,
                "firstName": "Test",
                "lastName": "Diagnostico",
                "enabled": True,
                "credentials": [{"type": "password", "value": "test1234", "temporary": False}]
            }
            
            create_response = requests.post(users_url, json=user_data, headers=headers, timeout=10)
            if create_response.status_code == 201:
                print(f"   ✅ Usuario de prueba creado exitosamente")
                print(f"   💡 Elimínalo manualmente desde Keycloak Admin Console: {test_email}")
            else:
                print(f"   ❌ Error creando usuario: {create_response.status_code}")
                print(f"   Respuesta: {create_response.text}")
    except Exception as e:
        print(f"   ⚠️  Error en prueba de creación: {e}")
    print()
    
    print("=" * 70)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 70)
    print()
    print("Si todos los checks pasaron ✅, la configuración es correcta.")
    print("Si hay errores ❌, revisa los mensajes y sigue las sugerencias 💡")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_keycloak_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnóstico interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        sys.exit(1)
