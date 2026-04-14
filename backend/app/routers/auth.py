from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from jose import JWTError

from app.core.security import create_access_token, decode_access_token, hash_password
from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    CreateUserRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    UserCreatedResponse,
    UserInToken,
)
from app.services.email import send_reset_password_email
from app.core.limiter import limiter
from app.core.keycloak_client import (
    is_keycloak_available,
    login_with_password,
    create_keycloak_user,
    assign_role_to_keycloak_user,
    delete_keycloak_user,
)

router = APIRouter()

_INVALID_CREDENTIALS = "Credenciales inválidas"


@router.post("/login", response_model=dict)
@limiter.limit("20/minute")
async def login(request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login directo contra Keycloak sin redirección (Password Grant).

    Retorna tokens OIDC válidos de Keycloak para consumo del frontend.
    """
    from app.services.recaptcha import verify_recaptcha
    from app.core.config import settings
    from keycloak.exceptions import KeycloakAuthenticationError, KeycloakError
    
    # Validar reCAPTCHA si está habilitado
    if settings.RECAPTCHA_ENABLED:
        client_ip = request.client.host if request.client else None
        is_valid = await verify_recaptcha(credentials.recaptcha_token, client_ip)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Validación de reCAPTCHA fallida. Por favor, intenta nuevamente.",
            )
    
    if not is_keycloak_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de autenticación no disponible. Por favor, intenta más tarde.",
        )

    # Verificar si el usuario existe en la BD local
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    # Si el usuario no existe en la BD local
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No existe ningún usuario con esas credenciales.",
        )
    
    # Si el usuario existe pero está inactivo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta ha sido desactivada. Contacta al coordinador.",
        )

    # Intentar autenticar con Keycloak
    try:
        tokens = login_with_password(credentials.email, credentials.password)
    except KeycloakAuthenticationError:
        # Error de autenticación específico (contraseña incorrecta)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La contraseña ingresada es incorrecta.",
        )
    except KeycloakError as e:
        # Otros errores de Keycloak
        error_msg = str(e).lower()
        if "invalid" in error_msg or "credentials" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Las credenciales ingresadas son incorrectas.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en el servicio de autenticación. Por favor, intenta más tarde.",
            )
    except Exception as e:
        # Error genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar sesión. Por favor, intenta más tarde.",
        )

    return {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens.get("expires_in"),
        "token_type": tokens.get("token_type", "bearer"),
        "has_completed_onboarding": user.has_completed_onboarding,
    }


_RESET_MESSAGE = "Si el email existe y está activo, recibirás un enlace para restablecer tu contraseña."


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Genera un token de reset de contraseña y envía email.

    - Si el email existe y está activo → genera token JWT de reset (exp: 1 hora), envía email
    - Si el email NO existe → retorna 200 con mismo mensaje genérico (no revelar si existe)
    """
    result = await db.execute(
        select(User).where(User.email == request.email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if user is not None:
        reset_token = create_access_token(
            {"sub": str(user.id), "role": user.role, "type": "reset"},
            expires_delta=timedelta(hours=1),
        )
        await send_reset_password_email(user.email, reset_token)

    return MessageResponse(message=_RESET_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Valida el token de reset y actualiza la contraseña.

    1. Decodifica el token con decode_access_token()
    2. Verifica que payload["type"] == "reset"
    3. Busca el usuario por payload["sub"]
    4. Actualiza user.hashed_password con hash_password(request.new_password)
    5. Retorna 200 con mensaje de éxito

    Si el token es inválido, expirado o no es de tipo "reset" → 400
    """
    try:
        payload = decode_access_token(request.token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

    if payload.get("type") != "reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

    user_id = payload.get("sub")
    from uuid import UUID

    try:
        user_uuid = UUID(str(user_id))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

    user.hashed_password = hash_password(request.new_password)
    await db.commit()

    return MessageResponse(message="Contraseña actualizada correctamente.")


@router.post("/complete-onboarding", response_model=MessageResponse)
async def complete_onboarding(
    current_user: UserInToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marca el onboarding como completado para el usuario autenticado.
    Idempotente: si ya estaba completado, no hace nada.
    """
    from uuid import UUID
    user_id = UUID(current_user.id)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and not user.has_completed_onboarding:
        user.has_completed_onboarding = True
        await db.commit()
    return MessageResponse(message="Onboarding completado.")


# ==========================================
# Endpoints OAuth2 / Keycloak (FASE 1)
# ==========================================

@router.post("/callback", response_model=dict)
async def oauth_callback(code: str, redirect_uri: str | None = None):
    """
    Endpoint de callback OAuth2 para intercambiar código de autorización por tokens.

    Este endpoint se usa en el flujo Authorization Code de OAuth2:
    1. El frontend redirige al usuario a Keycloak (/auth)
    2. Usuario ingresa credenciales en Keycloak
    3. Keycloak redirige de vuelta con un 'code' en la URL
    4. El frontend llama a este endpoint con el 'code'
    5. Se intercambia el code por access_token + refresh_token

    Args:
        code: Código de autorización obtenido de Keycloak
        redirect_uri: URI de redirección (opcional, usa la configurada por defecto)

    Returns:
        {
            "access_token": "...",
            "refresh_token": "...",
            "expires_in": 300,
            "token_type": "Bearer"
        }

    Raises:
        HTTPException(400): Si el código es inválido o ha expirado
    """
    from app.core.keycloak_client import exchange_code_for_token
    from app.core.config import settings

    try:
        redirect = redirect_uri or settings.KEYCLOAK_REDIRECT_URI
        tokens = exchange_code_for_token(code, redirect)
        return tokens
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de autorización inválido o expirado. Por favor, intenta iniciar sesión nuevamente."
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: str):
    """
    Renueva el access token usando un refresh token válido.

    Cuando el access token expira (típicamente después de 5 minutos),
    el frontend puede usar el refresh token para obtener uno nuevo
    sin requerir que el usuario vuelva a autenticarse.

    Args:
        refresh_token: Refresh token obtenido en /callback o /refresh previo

    Returns:
        {
            "access_token": "...",
            "refresh_token": "...",  # Nuevo refresh token
            "expires_in": 300
        }

    Raises:
        HTTPException(401): Si el refresh token es inválido o ha expirado
    """
    from app.core.keycloak_client import refresh_access_token

    try:
        tokens = refresh_access_token(refresh_token)
        return tokens
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tu sesión ha expirado. Por favor, inicia sesión nuevamente."
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(refresh_token: str):
    """
    Cierra la sesión del usuario invalidando el refresh token en Keycloak.

    Args:
        refresh_token: Refresh token del usuario a desloguear

    Returns:
        {"message": "Sesión cerrada correctamente"}

    Raises:
        HTTPException(400): Si hay un error en el logout
    """
    from app.core.keycloak_client import logout_user

    try:
        logout_user(refresh_token)
        return MessageResponse(message="Sesión cerrada correctamente")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al cerrar sesión. Por favor, intenta nuevamente."
        )


@router.post("/create-user", response_model=UserCreatedResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo usuario (estudiante o tutor).
    
    Solo los coordinadores pueden acceder a este endpoint.
    
    Proceso transaccional:
    1. Validar que el email no exista en la BD local
    2. Crear el usuario en Keycloak
    3. Asignar el rol en Keycloak
    4. Crear registro en la BD local
    5. Si algo falla, hacer rollback completo
    
    Args:
        user_data: CreateUserRequest con email, password, full_name, role
        current_user: Usuario autenticado (debe ser coordinador)
        db: Sesión de base de datos
    
    Returns:
        UserCreatedResponse con los datos del usuario creado
    
    Raises:
        HTTPException(400): Si el email ya existe, validación falla, etc.
        HTTPException(403): Si el usuario no es coordinador
        HTTPException(503): Si Keycloak no está disponible
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Coordinador {current_user.id} intenta crear usuario: {user_data.email} ({user_data.role})")
    
    # Verificar que Keycloak está disponible
    if not is_keycloak_available():
        logger.error("Keycloak no está disponible")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de autenticación no disponible. Por favor, intenta más tarde.",
        )
    
    # Verificar que el email no exista en la BD local
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        logger.warning(f"Email {user_data.email} ya existe en BD local")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El email {user_data.email} ya está registrado en el sistema"
        )
    
    keycloak_user_id = None
    try:
        # 1. Crear usuario en Keycloak
        names = user_data.full_name.strip().split(" ", 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ""
        
        logger.info(f"Paso 1: Creando usuario en Keycloak...")
        keycloak_user_id = create_keycloak_user(
            email=user_data.email,
            password=user_data.password,
            first_name=first_name,
            last_name=last_name
        )
        logger.info(f"Usuario creado en Keycloak con ID: {keycloak_user_id}")
        
        # 2. Asignar rol en Keycloak
        logger.info(f"Paso 2: Asignando rol {user_data.role}...")
        assign_role_to_keycloak_user(keycloak_user_id, user_data.role)
        logger.info(f"Rol asignado exitosamente")
        
        # 3. Crear usuario en BD local con el ID de Keycloak
        logger.info(f"Paso 3: Creando usuario en BD local con ID de Keycloak...")
        from uuid import UUID
        new_user = User(
            id=UUID(keycloak_user_id),  # Usar el ID de Keycloak
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            profession=user_data.profession if user_data.role == "tutor" else None,
            available_hours_per_week=(
                user_data.available_hours_per_week if user_data.role == "tutor" else None
            ),
            tutor_training_status=(
                user_data.tutor_training_status if user_data.role == "tutor" else None
            ),
            is_active=True,
            has_completed_onboarding=False,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"✅ Usuario {user_data.email} creado exitosamente (ID: {new_user.id})")
        
        return UserCreatedResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            profession=new_user.profession,
            available_hours_per_week=new_user.available_hours_per_week,
            tutor_training_status=new_user.tutor_training_status,
            message=f"Usuario {user_data.role} creado exitosamente"
        )
        
    except ValueError as e:
        # Error de validación (email duplicado en Keycloak, etc.)
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Si hay error, hacer rollback completo
        logger.error(f"❌ Error creando usuario: {e}")
        
        if keycloak_user_id:
            try:
                logger.info(f"Intentando rollback: eliminando usuario {keycloak_user_id} de Keycloak...")
                delete_keycloak_user(keycloak_user_id)
                logger.info("Rollback exitoso")
            except Exception as del_error:
                logger.error(f"Error en rollback de Keycloak: {del_error}")
                # El usuario quedará huérfano en Keycloak - requiere limpieza manual
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando usuario: {str(e)}"
        )
