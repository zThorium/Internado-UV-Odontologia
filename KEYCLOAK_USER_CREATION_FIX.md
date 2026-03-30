# Fix: Creación de Usuarios con Keycloak

## Problema Identificado

La funcionalidad de creación de usuarios por el coordinador no está funcionando correctamente. Después de analizar el código, identifiqué **3 problemas principales**:

### 1. Token de Admin Incorrecto
La función `_get_admin_access_token()` en `keycloak_client.py` intenta autenticarse contra el realm `internado-uv`, pero el usuario `admin` vive en el realm `master` de Keycloak.

**Código actual (INCORRECTO)**:
```python
token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
```

**Debe ser**:
```python
token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
```

### 2. Falta el ID de Keycloak en la BD
El modelo `User` no tiene un campo para almacenar el `keycloak_user_id`, lo que dificulta la sincronización entre Keycloak y la BD local.

### 3. Rollback Incompleto
Si falla la asignación del rol en Keycloak, el usuario queda creado pero sin rol asignado, lo que causa problemas de autenticación.

---

## Solución Implementada

### Paso 1: Fix del Token de Admin

**Archivo**: `backend/app/core/keycloak_client.py`

```python
def _get_admin_access_token() -> str:
    """
    Obtiene un access token administrativo de Keycloak.
    
    IMPORTANTE: El usuario admin vive en el realm 'master', no en 'internado-uv'.
    
    Returns:
        str: Access token para operaciones administrativas
    
    Raises:
        Exception: Si no se puede autenticar como admin
    """
    import requests
    
    # CORRECCIÓN: Autenticar contra el realm master
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
```

### Paso 2: Agregar Campo keycloak_id al Modelo User

**Archivo**: `backend/app/models/user.py`

Agregar el campo:
```python
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, UUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum("student", "tutor", "coordinator", name="user_role"), nullable=False)
    is_active = Column(Boolean, default=True)
    has_completed_onboarding = Column(Boolean, default=False)
    
    # NUEVO: ID del usuario en Keycloak para sincronización
    keycloak_id = Column(String, unique=True, nullable=True, index=True)
```

**Crear migración**:
```bash
cd backend
alembic revision --autogenerate -m "add keycloak_id to users"
alembic upgrade head
```

### Paso 3: Actualizar el Endpoint de Creación

**Archivo**: `backend/app/routers/auth.py`

```python
@router.post("/create-user", response_model=UserCreatedResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: UserInToken = Depends(require_role("coordinator")),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo usuario (estudiante o tutor).
    
    Proceso transaccional:
    1. Validar que el email no exista en la BD local
    2. Crear el usuario en Keycloak
    3. Asignar el rol en Keycloak
    4. Crear registro en la BD local con keycloak_id
    5. Si algo falla, hacer rollback completo
    """
    
    # Verificar que Keycloak está disponible
    if not is_keycloak_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de autenticación no disponible. Verifica que Keycloak esté corriendo.",
        )
    
    # Verificar que el email no exista en la BD local
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
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
        
        logger.info(f"Creando usuario en Keycloak: {user_data.email}")
        keycloak_user_id = create_keycloak_user(
            email=user_data.email,
            password=user_data.password,
            first_name=first_name,
            last_name=last_name
        )
        logger.info(f"Usuario creado en Keycloak con ID: {keycloak_user_id}")
        
        # 2. Asignar rol en Keycloak
        logger.info(f"Asignando rol {user_data.role} al usuario {keycloak_user_id}")
        assign_role_to_keycloak_user(keycloak_user_id, user_data.role)
        logger.info(f"Rol asignado exitosamente")
        
        # 3. Crear usuario en BD local
        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True,
            has_completed_onboarding=False,
            keycloak_id=keycloak_user_id  # NUEVO: Guardar ID de Keycloak
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"Usuario {user_data.email} creado exitosamente en BD local")
        
        return UserCreatedResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
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
        logger.error(f"Error creando usuario: {e}")
        
        if keycloak_user_id:
            try:
                logger.info(f"Intentando eliminar usuario {keycloak_user_id} de Keycloak (rollback)")
                delete_keycloak_user(keycloak_user_id)
                logger.info("Rollback exitoso")
            except Exception as del_error:
                logger.error(f"Error en rollback de Keycloak: {del_error}")
                # El usuario quedará huérfano en Keycloak - requiere limpieza manual
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando usuario: {str(e)}"
        )
```

---

## Verificación y Testing

### 1. Verificar que Keycloak está corriendo
```bash
curl http://localhost:8080/realms/master/.well-known/openid-configuration
```

### 2. Verificar que los roles existen en Keycloak
- Ir a http://localhost:8080/admin
- Login con admin/admin123
- Ir a Realm `internado-uv` → Realm roles
- Verificar que existen: `student`, `tutor`, `coordinator`

### 3. Probar el endpoint desde el frontend
1. Login como coordinador
2. Ir a "Crear Usuario"
3. Llenar el formulario:
   - Email: test@uv.cl
   - Nombre: Test Usuario
   - Contraseña: test1234
   - Rol: student
4. Click en "Crear usuario"

### 4. Verificar en Keycloak
- Ir a Users en Keycloak
- Buscar test@uv.cl
- Verificar que tiene el rol `student` asignado

### 5. Verificar en la BD
```sql
SELECT id, email, full_name, role, keycloak_id FROM users WHERE email = 'test@uv.cl';
```

---

## Troubleshooting

### Error: "Keycloak no está disponible"
- Verificar que Keycloak está corriendo: `docker ps | grep keycloak`
- Verificar la URL en `.env`: `KEYCLOAK_SERVER_URL=http://localhost:8080`

### Error: "Rol 'student' no existe en Keycloak"
- Crear los roles manualmente en Keycloak Admin Console
- O ejecutar el script de migración: `python -m scripts.migrate_to_keycloak`

### Error: "El usuario ya existe"
- Verificar en Keycloak si el usuario existe
- Si existe pero no está en la BD, agregar manualmente con el `keycloak_id`

### Error: "Error obteniendo token de admin"
- Verificar credenciales en `.env`:
  - `KEYCLOAK_ADMIN_USERNAME=admin`
  - `KEYCLOAK_ADMIN_PASSWORD=admin123`
- Verificar que el usuario admin existe en el realm `master`

---

## Próximos Pasos

1. **Implementar sincronización bidireccional**: Si un usuario se modifica en Keycloak, actualizar la BD local
2. **Agregar endpoint de actualización de usuario**: Permitir al coordinador cambiar roles o desactivar usuarios
3. **Implementar búsqueda de usuarios**: Endpoint para listar todos los usuarios creados
4. **Agregar validaciones adicionales**: Email institucional (@uv.cl), contraseñas seguras, etc.
5. **Implementar auditoría**: Registrar quién creó cada usuario y cuándo

