# Guía de Configuración de Keycloak

Esta guía detalla cómo configurar Keycloak para el proyecto Internado Odontología UV.

## Tabla de Contenidos

- [1. Prerequisitos](#1-prerequisitos)
- [2. Levantar Keycloak](#2-levantar-keycloak)
- [3. Acceder a Admin Console](#3-acceder-a-admin-console)
- [4. Crear Realm](#4-crear-realm)
- [5. Configurar Roles](#5-configurar-roles)
- [6. Crear Clients](#6-crear-clients)
- [7. Migrar Usuarios](#7-migrar-usuarios)
- [8. Probar Autenticación](#8-probar-autenticación)
- [9. Configuración Avanzada](#9-configuración-avanzada)

---

## 1. Prerequisitos

Asegúrate de tener:
- Docker y Docker Compose instalados
- PostgreSQL corriendo (puerto 5433)
- Backend configurado con las variables de entorno de Keycloak

## 2. Levantar Keycloak

### Opción A: Con dev.sh (Recomendado)

```bash
./dev.sh
```

Esto levantará automáticamente:
- PostgreSQL
- **Keycloak** (http://localhost:8080)
- Redis
- MinIO

### Opción B: Solo Keycloak

```bash
docker compose up -d db keycloak
```

### Verificar que Keycloak está corriendo

```bash
# Verificar health check
curl http://localhost:8080/health/ready

# Debe retornar status 200 cuando esté listo (puede tomar 60-90 segundos)
```

---

## 3. Acceder a Admin Console

1. Abre http://localhost:8080 en tu navegador
2. Click en **"Administration Console"**
3. Ingresa credenciales de admin:
   - **Username**: `admin`
   - **Password**: `admin123`

---

## 4. Crear Realm

Un **realm** es como un "tenant" en Keycloak. Vamos a crear uno específico para nuestra aplicación.

### Pasos:

1. En el dropdown superior izquierdo (dice "master"), haz click
2. Click en **"Create realm"**
3. Configuración:
   - **Realm name**: `internado-uv`
   - **Enabled**: ON
4. Click en **"Create"**

✅ **Ahora deberías ver "internado-uv" en el dropdown superior**

---

## 5. Configurar Roles

Vamos a crear los 3 roles de la aplicación: **student**, **tutor**, **coordinator**.

### Pasos:

1. En el menú lateral izquierdo, click en **"Realm roles"**
2. Click en **"Create role"**
3. Crear el rol **student**:
   - **Role name**: `student`
   - **Description**: `Estudiante de internado`
   - Click **"Save"**
4. Repetir para crear:
   - **tutor**: `tutor` / `Tutor clínico`
   - **coordinator**: `coordinator` / `Coordinador de internado`

✅ **Deberías tener 3 roles creados**

---

## 6. Crear Clients

Los **clients** representan las aplicaciones que se autenticarán contra Keycloak.

### 6.1. Client del Backend (confidencial)

1. En el menú lateral, click en **"Clients"**
2. Click en **"Create client"**
3. **General Settings**:
   -Client type**: `OpenID Connect`
   - **Client ID**: `internado-backend`
   - Click **"Next"**
4. **Capability config**:
   - **Client authentication**: ON (confidencial client)
   - **Authorization**: OFF
   - **Authentication flow**:
     - ✅ Standard flow
     - ✅ Direct access grants
     - ❌ Implicit flow
     - ✅ Service accounts roles
   - Click **"Next"**
5. **Login settings**:
   - **Root URL**: `http://localhost:8000`
   - **Valid redirect URIs**: `http://localhost:5173/*`
   - **Web origins**: `http://localhost:5173`
   - Click **"Save"**
6. Ir a la pestaña **"Credentials"**
7. **Copiar el Client Secret** y pegarlo en `backend/.env`:
   ```env
   KEYCLOAK_CLIENT_SECRET=tu-client-secret-aqui
   ```

### 6.2. Client del Frontend (público)

1. Click en **"Create client"** nuevamente
2. **General Settings**:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `internado-frontend`
   - Click **"Next"**
3. **Capability config**:
   - **Client authentication**: OFF (público client)
   - **Authorization**: OFF
   - **Authentication flow**:
     - ✅ Standard flow
     - ❌ Direct access grants
     - ❌ Implicit flow
   - Click **"Next"**
4. **Login settings**:
   - **Root URL**: `http://localhost:5173`
   - **Valid redirect URIs**:
     - `http://localhost:5173/*`
     - `http://localhost:5173/callback`
   - **Valid post logout redirect URIs**: `http://localhost:5173`
   - **Web origins**: `http://localhost:5173`
   - Click **"Save"**
5. Ir a la pestaña **"Advanced"** → **"Advanced Settings"**
6. **Proof Key for Code Exchange (PKCE)**:
   - **PKCE Code Challenge Method**: `S256`
   - Click **"Save"**

✅ **Deberías tener 2 clients creados: internado-backend e internado-frontend**

---

## 7. Migrar Usuarios

Ahora vamos a migrar los usuarios existentes de PostgreSQL a Keycloak.

### Verificar que tienes usuarios en PostgreSQL

```bash
cd backend
python -m scripts.seed  # Si no has corrido el seed aún
```

### Ejecutar script de migración

```bash
cd backend
python -m scripts.migrate_to_keycloak
```

El script:
1. Conecta a Keycloak y PostgreSQL
2. Crea cada usuario en Keycloak
3. Asigna el rol correspondiente (student, tutor, coordinator)
4. Configura contraseña temporal: `changeme123`

### Verificar usuarios en Keycloak

1. En Admin Console, ir a **"Users"**
2. Click en **"View all users"**
3. Deberías ver:
   - `coord@internado-uv.cl` (coordinator)
   - `tutor@internado-uv.cl` (tutor)
   - `estudiante@internado-uv.cl` (student)

### Ver roles asignados a un usuario

1. Click en un usuario
2. Pestaña **"Role mapping"**
3. Deberías ver su rol asignado en **"Assigned roles"**

---

## 8. Probar Autenticación

### Probar con el backend

```bash
# Levantar backend
cd backend
uvicorn app.main:app --reload

# En otra terminal, probar login con Keycloak
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "estudiante@internado-uv.cl",
    "password": "estudiante123"
  }'

# Debería retornar un access_token
```

### Probar desde el frontend

1. Levantar frontend: `cd frontend && npm run dev`
2. Abrir http://localhost:5173
3. Intentar login (todavía usa JWT legacy)
4. Después de implementar la integración React-Keycloak, podrás probar el flujo OAuth2

---

## 9. Configuración Avanzada

### 9.1. Configurar Token Lifespan

Por defecto, los access tokens expiran en 5 minutos. Puedes ajustarlo:

1. En el menú lateral, ir a **"Realm settings"**
2. Pestaña **"Tokens"**
3. Ajustar:
   - **Access Token Lifespan**: `5` minutos (recomendado)
   - **Refresh Token Max Reuse**: `0` (refresh token solo se usa 1 vez)
   - **SSO Session Idle**: `30` minutos
   - **SSO Session Max**: `10` horas
4. Click **"Save"**

### 9.2. Habilitar MFA (Opcional)

Para habilitar autenticación de dos factores:

1. **Realm settings** → **Authentication**
2. Pestaña **"Required actions"**
3. Habilitar **"Configure OTP"**
4. Los usuarios deberán configurar TOTP en su próximo login

### 9.3. Configurar Email (Opcional)

Para enviar emails de verificación y reset de contraseña:

1. **Realm settings** → **Email**
2. Configurar SMTP:
   ```
   Host: smtp.gmail.com
   Port: 587
   From: noreply@internado-uv.cl
   Enable StartTLS: ON
   Username: tu-email@gmail.com
   Password: tu-app-password
   ```
3. Click **"Save"** y luego **"Test connection"**

### 9.4. Personalizar Temas (Opcional)

Para personalizar la página de login:

1. **Realm settings** → **Themes**
2. **Login theme**: Puedes crear uno custom o usar los predefinidos
3. **Email theme**: Para personalizar emails

---

## 10. Troubleshooting

### Keycloak no inicia / healthcheck falla

```bash
# Ver logs
docker logs -f internado_uv_keycloak

# Verificar que PostgreSQL esté corriendo
docker compose ps db

# Reiniciar Keycloak
docker compose restart keycloak
```

### Error "Invalid client credentials"

- Verifica que el `KEYCLOAK_CLIENT_SECRET` en `.env` coincida con el de Keycloak
- Ir a **Clients** → **internado-backend** → **Credentials** → copiar secret

### Error "Redirect URI mismatch"

- Verifica que las URIs en Keycloak coincidan con las configuradas
- En Clients → internado-frontend → **Valid redirect URIs** debe incluir `http://localhost:5173/*`

### Usuarios no pueden autenticarse

1. Verificar que el usuario exista: **Users** → buscar por email
2. Verificar que esté habilitado: **User** → toggle **Enabled** debe estar ON
3. Verificar roles: **User** → **Role mapping**
4. Resetear contraseña: **User** → **Credentials** → **Reset password**

---

## 11. Comandos Útiles

```bash
# Levantar solo Keycloak
docker compose up -d keycloak

# Ver logs de Keycloak
docker logs -f internado_uv_keycloak

# Detener Keycloak
docker compose stop keycloak

# Resetear Keycloak (eliminar todos los datos)
docker compose down -v
docker compose up -d db keycloak

# Exportar configuración del realm
# (útil para backup o despliegue en producción)
docker exec internado_uv_keycloak \
  /opt/keycloak/bin/kc.sh export \
  --realm internado-uv \
  --file /tmp/realm-export.json

# Copiar export al host
docker cp internado_uv_keycloak:/tmp/realm-export.json ./keycloak-realm-export.json
```

---

## 12. Próximos Pasos

Una vez configurado Keycloak:

1. ✅ Implementar integración en el frontend con `@react-keycloak/web`
2. ✅ Actualizar `AuthContext` para usar Keycloak en lugar de JWT manual
3. ✅ Configurar auto-refresh de tokens en axios
4. ✅ Migrar todos los usuarios existentes
5. ✅ Probar flujo completo de login/logout
6. ✅ Escribir tests de integración

---

## Referencias

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Specs](https://openid.net/connect/)
- [python-keycloak Library](https://github.com/marcospereirampj/python-keycloak)
- [react-keycloak Library](https://github.com/react-keycloak/react-keycloak)
