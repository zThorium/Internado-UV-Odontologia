from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import logging

from app.schemas.auth import UserInToken
from app.core.keycloak_client import (
    validate_token,
    decode_token,
    get_primary_role,
    is_keycloak_available
)

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _looks_like_keycloak_token(token: str) -> bool:
    """Heurística barata para decidir si el token proviene de Keycloak/OIDC."""
    try:
        claims = jwt.get_unverified_claims(token)
    except Exception:
        return False

    iss = claims.get("iss")
    if isinstance(iss, str) and "/realms/" in iss:
        return True

    if "realm_access" in claims:
        return True

    return False


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInToken:
    """
    Dependencia FastAPI que extrae y valida el JWT del header Authorization.

    Estrategia de autenticación:
    1. Acepta solo tokens OIDC de Keycloak
    2. Rechaza tokens JWT legacy

    Returns:
        UserInToken con id y role del usuario autenticado

    Raises:
        HTTPException(401): Si el token es inválido o expirado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not _looks_like_keycloak_token(token):
        logger.warning("Token no OIDC rechazado (legacy deshabilitado)")
        raise credentials_exception

    if not is_keycloak_available():
        logger.error("Keycloak no disponible para validar token")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de autenticación no disponible",
        )

    try:
        token_info = validate_token(token)

        if not token_info.get("active"):
            raise credentials_exception

        # Decode the JWT token to get claims including realm_access.roles
        token_claims = decode_token(token, validate=False)
        user_id = token_claims.get("sub")
        role = get_primary_role(token_claims)

        if not user_id or not role:
            logger.warning(f"Token Keycloak válido pero sin user_id o role: {token_claims}")
            raise credentials_exception

        logger.debug(f"Usuario autenticado con Keycloak: {user_id} ({role})")
        return UserInToken(id=user_id, role=role)

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Fallo autenticación Keycloak: {e}")
        raise credentials_exception


def require_role(*allowed_roles: str):
    """
    Factory de dependencias FastAPI que verifica el rol del usuario.

    Uso en router:
        @router.get("/endpoint")
        async def endpoint(user: UserInToken = Depends(require_role("student", "coordinator"))):
            ...

    Postcondiciones (del diseño):
    - Si user.role in allowed_roles → retorna UserInToken
    - Si user.role NOT in allowed_roles → lanza HTTPException(403)
    - Regla crítica: tutores que intentan acceder a /logbook o /incidents reciben 403, no 404
    """
    async def role_checker(current_user: UserInToken = Depends(get_current_user)) -> UserInToken:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado",
            )
        return current_user
    return role_checker
