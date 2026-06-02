"""
Cliente de Keycloak para autenticación OIDC.

Este módulo proporciona funciones para interactuar con Keycloak:
- Validación de tokens OIDC
- Obtención de información de usuario
- Introspección de tokens
- Intercambio de código de autorización por tokens
- Refresh de tokens
"""

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from typing import Dict, Optional
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

_KEYCLOAK_AVAILABILITY_TTL_SECONDS = 30
_keycloak_availability_cache: dict[str, float | bool | None] = {
    "value": None,
    "checked_at": 0.0,
}

# Cliente Keycloak OpenID
keycloak_openid = KeycloakOpenID(
    server_url=settings.KEYCLOAK_SERVER_URL,
    client_id=settings.KEYCLOAK_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM,
    client_secret_key=settings.KEYCLOAK_CLIENT_SECRET if settings.KEYCLOAK_CLIENT_SECRET else None,
    timeout=settings.KEYCLOAK_REQUEST_TIMEOUT_SECONDS,
)


def validate_token(token: str) -> Dict:
    """
    Valida un token de Keycloak usando introspection.

    Args:
        token: Access token JWT de Keycloak

    Returns:
        Dict con información del token (active, exp, sub, roles, etc.)

    Raises:
        KeycloakError: Si el token es inválido o ha expirado
    """
    try:
        token_info = keycloak_openid.introspect(token)

        if not token_info.get("active"):
            raise ValueError("Token inactivo o expirado")

        return token_info
    except ValueError as e:
        logger.debug(f"Token Keycloak no activo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error validando token Keycloak: {e}")
        raise


def get_user_info(token: str) -> Dict:
    """
    Obtiene información del usuario desde Keycloak usando el token.

    Args:
        token: Access token JWT válido

    Returns:
        Dict con información del usuario (sub, email, name, roles, etc.)

    Raises:
        KeycloakError: Si el token es inválido o el servidor no responde
    """
    try:
        return keycloak_openid.userinfo(token)
    except Exception as e:
        logger.error(f"Error obteniendo info de usuario: {e}")
        raise


def exchange_code_for_token(code: str, redirect_uri: str) -> Dict:
    """
    Intercambia un código de autorización por tokens (access + refresh).

    Este método se usa en el flujo OAuth2 Authorization Code.

    Args:
        code: Código de autorización obtenido del callback
        redirect_uri: URI de redirección (debe coincidir con la configurada en Keycloak)

    Returns:
        Dict con: access_token, refresh_token, expires_in, token_type, etc.

    Raises:
        KeycloakError: Si el código es inválido o ha expirado
    """
    try:
        return keycloak_openid.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri=redirect_uri
        )
    except Exception as e:
        logger.error(f"Error intercambiando código por token: {e}")
        raise


def login_with_password(username: str, password: str) -> Dict:
    """
    Obtiene tokens de Keycloak usando credenciales (Direct Access Grant).

    Args:
        username: Username o email del usuario en Keycloak
        password: Contraseña del usuario

    Returns:
        Dict con access_token, refresh_token, expires_in y token_type

    Raises:
        KeycloakError: Si las credenciales son inválidas o el flujo está deshabilitado
    """
    try:
        return keycloak_openid.token(
            grant_type="password",
            username=username,
            password=password,
            scope="openid",
        )
    except Exception as e:
        logger.error(f"Error en login directo con Keycloak: {e}")
        raise


def refresh_access_token(refresh_token: str) -> Dict:
    """
    Renueva el access token usando un refresh token válido.

    Args:
        refresh_token: Refresh token obtenido previamente

    Returns:
        Dict con: access_token, expires_in, refresh_token (nuevo), etc.

    Raises:
        KeycloakError: Si el refresh token es inválido o ha expirado
    """
    try:
        return keycloak_openid.refresh_token(refresh_token)
    except Exception as e:
        logger.error(f"Error refrescando token: {e}")
        raise


def logout_user(refresh_token: str) -> None:
    """
    Realiza logout del usuario invalidando el refresh token.

    Args:
        refresh_token: Refresh token del usuario a desloguear

    Raises:
        KeycloakError: Si hay un error en el logout
    """
    try:
        keycloak_openid.logout(refresh_token)
        logger.info("Usuario deslogueado exitosamente")
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        raise


def decode_token(token: str, validate: bool = True) -> Dict:
    """
    Decodifica un JWT sin validarlo (útil para debugging).

    Args:
        token: JWT a decodificar
        validate: Si True, valida la firma del token

    Returns:
        Dict con los claims del token (sub, exp, iat, roles, etc.)
    """
    from jose import jwt

    try:
        if validate:
            # Get Keycloak's public key and format it properly
            public_key_raw = keycloak_openid.public_key()

            # Format the public key in PEM format if needed
            if not public_key_raw.startswith("-----BEGIN"):
                public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key_raw}\n-----END PUBLIC KEY-----"
            else:
                public_key = public_key_raw

            # Decode and validate token with Keycloak's public key
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=None,  # Don't verify audience
                options={"verify_aud": False}  # Explicitly disable audience verification
            )
            return decoded
        else:
            # Just decode without validation (faster, use when token is already validated)
            return jwt.get_unverified_claims(token)
    except Exception as e:
        logger.error(f"Error decodificando token: {e}")
        raise


def extract_roles(user_info: Dict) -> list[str]:
    """
    Extrae los roles del usuario desde la información de Keycloak.

    Args:
        user_info: Dict retornado por get_user_info() o decode_token()

    Returns:
        Lista de roles asignados al usuario
    """
    realm_access = user_info.get("realm_access", {})
    roles = realm_access.get("roles", [])

    # Filtrar solo los roles relevantes de la aplicación
    app_roles = ["student", "tutor", "coordinator"]
    return [role for role in roles if role in app_roles]


def get_primary_role(user_info: Dict) -> Optional[str]:
    """
    Obtiene el rol principal del usuario (el primero encontrado).

    Args:
        user_info: Dict con información del usuario

    Returns:
        Rol principal (student, tutor o coordinator) o None
    """
    roles = extract_roles(user_info)
    return roles[0] if roles else None


def is_keycloak_available() -> bool:
    """
    Verifica si Keycloak está disponible y responde.

    Returns:
        True si Keycloak está disponible, False en caso contrario
    """
    now = time.monotonic()
    cached_value = _keycloak_availability_cache["value"]
    checked_at = float(_keycloak_availability_cache["checked_at"] or 0.0)

    if cached_value is not None and (now - checked_at) < _KEYCLOAK_AVAILABILITY_TTL_SECONDS:
        return bool(cached_value)

    try:
        keycloak_openid.well_known()
        _keycloak_availability_cache["value"] = True
        _keycloak_availability_cache["checked_at"] = now
        return True
    except Exception as e:
        logger.warning(f"Keycloak no disponible: {e}")
        _keycloak_availability_cache["value"] = False
        _keycloak_availability_cache["checked_at"] = now
        return False


# ==========================================
# Admin Functions - User Management
# ==========================================

def get_keycloak_admin():
    """
    Obtiene una instancia del cliente de administración de Keycloak.
    
    Returns:
        KeycloakAdmin: Cliente configurado para operaciones administrativas
        
    Raises:
        Exception: Si no se puede conectar con Keycloak
    """
    from keycloak import KeycloakAdmin
    
    try:
        admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_SERVER_URL,
            username=settings.KEYCLOAK_ADMIN_USERNAME,
            password=settings.KEYCLOAK_ADMIN_PASSWORD,
            realm_name=settings.KEYCLOAK_REALM,
            user_realm_name="master",  # El usuario admin vive en el realm master
            verify=True
        )
        return admin
    except Exception as e:
        logger.error(f"Error creando cliente admin de Keycloak: {e}")
        raise


def _get_admin_access_token() -> str:
    """
    Obtiene un access token administrativo de Keycloak.
    
    IMPORTANTE: El usuario admin vive en el realm 'master', no en el realm de la aplicación.

    Returns:
        str: Access token para operaciones administrativas

    Raises:
        Exception: Si no se puede autenticar como admin
    """
    import requests
    
    # CORRECCIÓN: Autenticar contra el realm master donde vive el usuario admin
    token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
    
    try:
        response = requests.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,
                "username": settings.KEYCLOAK_ADMIN_USERNAME,
                "password": settings.KEYCLOAK_ADMIN_PASSWORD,
            },
            timeout=10  # Aumentar timeout a 10s
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.Timeout:
        logger.error("Timeout al conectar con Keycloak")
        raise Exception("Keycloak no responde (timeout)")
    except requests.exceptions.ConnectionError:
        logger.error("No se puede conectar con Keycloak")
        raise Exception("Keycloak no está disponible")
    except Exception as e:
        logger.error(f"Error obteniendo token de admin: {e}")
        raise


def create_keycloak_user(email: str, password: str, first_name: str, last_name: str = "") -> str:
    """
    Crea un nuevo usuario en Keycloak usando la API de administración.

    Args:
        email: Email del usuario (debe ser único)
        password: Contraseña en texto plano
        first_name: Nombre del usuario
        last_name: Apellido del usuario (opcional)

    Returns:
        str: ID del usuario creado en Keycloak

    Raises:
        ValueError: Si el usuario ya existe
        Exception: Si hay error al crear el usuario
    """
    import requests
    
    try:
        # Obtener token de admin
        logger.info("Obteniendo token de admin de Keycloak...")
        admin_token = _get_admin_access_token()
        logger.info("Token de admin obtenido exitosamente")
        
        # URL para crear usuario
        users_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
        
        # Headers con autenticación
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # Verificar si el usuario ya existe
        logger.info(f"Verificando si {email} ya existe en Keycloak...")
        check_url = f"{users_url}?email={email}"
        check_response = requests.get(check_url, headers=headers, timeout=10)
        check_response.raise_for_status()
        
        if check_response.json():
            logger.warning(f"Usuario {email} ya existe en Keycloak")
            raise ValueError(f"El usuario con email {email} ya existe en Keycloak")
        
        # Datos del nuevo usuario
        user_data = {
            "email": email,
            "username": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": False,
            "credentials": [
                {
                    "type": "password",
                    "value": password,
                    "temporary": False
                }
            ]
        }
        
        # Crear usuario
        logger.info(f"Creando usuario {email} en Keycloak...")
        response = requests.post(users_url, json=user_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            # Extraer ID de la locación en el header
            location = response.headers.get("location", "")
            user_id = location.split("/")[-1] if location else None
            
            if user_id:
                logger.info(f"Usuario creado en Keycloak: {email} (ID: {user_id})")
                return user_id
            else:
                raise Exception("No se pudo extraer el ID del usuario creado")
        elif response.status_code == 409:
            raise ValueError(f"El usuario con email {email} ya existe")
        else:
            error_detail = response.json() if response.text else response.reason
            logger.error(f"Error Keycloak ({response.status_code}): {error_detail}")
            raise Exception(f"Error Keycloak ({response.status_code}): {error_detail}")
            
    except ValueError as e:
        logger.warning(f"Validación: {e}")
        raise
    except requests.exceptions.Timeout:
        logger.error("Timeout al crear usuario en Keycloak")
        raise Exception("Keycloak no responde (timeout)")
    except requests.exceptions.ConnectionError:
        logger.error("No se puede conectar con Keycloak")
        raise Exception("Keycloak no está disponible")
    except Exception as e:
        logger.error(f"Error al crear usuario {email}: {e}")
        raise


def assign_role_to_keycloak_user(user_id: str, role_name: str) -> None:
    """
    Asigna un rol de reino a un usuario en Keycloak.

    Args:
        user_id: ID del usuario en Keycloak
        role_name: Nombre del rol (student, tutor, coordinator)

    Raises:
        Exception: Si hay error al asignar el rol
    """
    import requests
    
    try:
        # Obtener token de admin
        admin_token = _get_admin_access_token()
        
        # Headers con autenticación
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # Obtener todos los roles del reino
        roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/roles"
        roles_response = requests.get(roles_url, headers=headers, timeout=5)
        roles_response.raise_for_status()
        
        # Buscar el rol
        roles = roles_response.json()
        role = next((r for r in roles if r["name"] == role_name), None)
        
        if not role:
            raise ValueError(f"Rol {role_name} no existe en Keycloak")
        
        # Asignar el rol al usuario
        assign_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm"
        assign_response = requests.post(assign_url, json=[role], headers=headers, timeout=5)
        assign_response.raise_for_status()
        
        logger.info(f"Rol {role_name} asignado al usuario {user_id}")
        
    except ValueError as e:
        logger.warning(f"Validación: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al asignar rol: {e}")
        raise


def delete_keycloak_user(user_id: str) -> None:
    """
    Elimina un usuario de Keycloak.

    Args:
        user_id: ID del usuario en Keycloak

    Raises:
        Exception: Si hay error al eliminar el usuario
    """
    import requests
    
    try:
        # Obtener token de admin
        admin_token = _get_admin_access_token()
        
        # Headers con autenticación
        headers = {
            "Authorization": f"Bearer {admin_token}"
        }
        
        # Eliminar usuario
        delete_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}"
        response = requests.delete(delete_url, headers=headers, timeout=5)
        response.raise_for_status()
        
        logger.info(f"Usuario {user_id} eliminado de Keycloak")
        
    except Exception as e:
        logger.error(f"Error al eliminar usuario {user_id}: {e}")
        raise
