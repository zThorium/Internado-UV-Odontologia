# Fix: Tutores no ven estudiantes asignados

## Problema

Los tutores no pueden ver los estudiantes que se les asignaron. Esto ocurre porque:

1. Cuando se crea un usuario (tutor/estudiante) mediante el coordinador, se genera un UUID automático en la BD local
2. El usuario también se crea en Keycloak con un UUID diferente
3. Cuando el usuario se loguea, el token contiene el UUID de Keycloak
4. Las asignaciones se crean con el UUID de la BD local
5. Al buscar asignaciones por tutor_id, no coinciden los IDs

## Solución Implementada

### 1. Sincronización de IDs en nuevos usuarios

Se modificó el endpoint `/auth/create-user` para que use el ID de Keycloak como ID en la BD local:

```python
# backend/app/routers/auth.py
new_user = User(
    id=UUID(keycloak_user_id),  # Usar el ID de Keycloak
    email=user_data.email,
    # ... resto de campos
)
```

### 2. Fix del onboarding

Se corrigió el endpoint `/auth/complete-onboarding` para convertir correctamente el ID a UUID:

```python
from uuid import UUID
user_id = UUID(current_user.id)
result = await db.execute(select(User).where(User.id == user_id))
```

### 3. Script de migración para usuarios existentes

Se creó el script `backend/scripts/sync_keycloak_ids.py` que:
- Busca todos los usuarios en la BD local
- Obtiene sus IDs correspondientes en Keycloak
- Actualiza los IDs en la BD local y todas las tablas relacionadas

## Pasos para Resolver

### Opción A: Migrar usuarios existentes (Recomendado si ya tienes datos)

1. **Hacer backup de la base de datos**:
   ```bash
   # Desde el directorio raíz del proyecto
   docker exec -it internado-postgres pg_dump -U user internado_uv > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Ejecutar el script de sincronización**:
   ```bash
   cd backend
   python scripts/sync_keycloak_ids.py
   ```

3. **Verificar que funcionó**:
   - Inicia sesión como tutor
   - Ve a "Mis estudiantes"
   - Deberías ver los estudiantes asignados

### Opción B: Recrear usuarios (Si no tienes datos importantes)

1. **Eliminar usuarios existentes de Keycloak**:
   - Ve a http://localhost:8080/admin
   - Login: admin / admin123
   - Realm: internado-uv
   - Users → Elimina los usuarios creados (excepto admin)

2. **Limpiar la base de datos**:
   ```bash
   cd backend
   # Eliminar y recrear las tablas
   alembic downgrade base
   alembic upgrade head
   python scripts/seed.py
   ```

3. **Recrear usuarios desde el coordinador**:
   - Los nuevos usuarios ya tendrán IDs sincronizados

## Verificación

Después de aplicar la solución:

1. **Login como coordinador**
2. **Crear una nueva asignación** (o verificar las existentes)
3. **Login como tutor**
4. **Ir a "Mis estudiantes"** → Deberías ver los estudiantes asignados
5. **Completar el tour de bienvenida** → No debería aparecer de nuevo

## Cambios Realizados

### Backend

- `backend/app/routers/auth.py`:
  - Endpoint `/auth/create-user`: Usa ID de Keycloak en BD local
  - Endpoint `/auth/complete-onboarding`: Convierte ID a UUID correctamente

- `backend/app/services/evaluations.py`:
  - Agregado campo `email` al retorno de `get_assigned_students()`
  - Convertir IDs a strings para consistencia

- `backend/app/schemas/evaluations.py`:
  - Agregado campo `email` al schema `StudentSummary`

- `backend/scripts/sync_keycloak_ids.py`:
  - Nuevo script para migrar IDs existentes

### Frontend

- Sin cambios necesarios (ya funcionaba correctamente)

## Notas Importantes

- **Nuevos usuarios**: Automáticamente tendrán IDs sincronizados
- **Usuarios existentes**: Necesitan ejecutar el script de migración
- **Backup**: Siempre hacer backup antes de ejecutar el script de migración
- **Keycloak**: Debe estar corriendo para que el script funcione
