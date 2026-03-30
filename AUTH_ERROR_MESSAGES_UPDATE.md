# Mensajes de Error de Autenticación - Actualización

## Resumen
Se han personalizado todos los mensajes de error de autenticación para que sean más naturales y no mencionen "Keycloak" u otros detalles técnicos internos.

## Cambios Realizados

### Endpoint `/auth/login`

#### Antes:
- Error genérico: "Credenciales inválidas"
- No diferenciaba entre usuario inexistente y contraseña incorrecta
- Mencionaba "Keycloak" en algunos errores

#### Después:
Mensajes específicos según el tipo de error:

1. **Usuario no existe**:
   ```
   "No existe ningún usuario con esas credenciales."
   ```
   - Status: 401 Unauthorized
   - Se verifica primero en la BD local

2. **Cuenta desactivada**:
   ```
   "Tu cuenta ha sido desactivada. Contacta al coordinador."
   ```
   - Status: 403 Forbidden
   - Indica claramente que debe contactar al coordinador

3. **Contraseña incorrecta**:
   ```
   "La contraseña ingresada es incorrecta."
   ```
   - Status: 401 Unauthorized
   - Captura específicamente `KeycloakAuthenticationError`

4. **Credenciales incorrectas (genérico)**:
   ```
   "Las credenciales ingresadas son incorrectas."
   ```
   - Status: 401 Unauthorized
   - Para otros errores de Keycloak relacionados con credenciales

5. **Servicio no disponible**:
   ```
   "Servicio de autenticación no disponible. Por favor, intenta más tarde."
   ```
   - Status: 503 Service Unavailable
   - Cuando Keycloak no está disponible

6. **Error genérico**:
   ```
   "Error al iniciar sesión. Por favor, intenta más tarde."
   ```
   - Status: 500 Internal Server Error
   - Para errores inesperados

### Endpoint `/auth/refresh`

#### Antes:
```
"Error refrescando token: {error_técnico}"
```

#### Después:
```
"Tu sesión ha expirado. Por favor, inicia sesión nuevamente."
```
- Status: 401 Unauthorized
- Mensaje claro y accionable

### Endpoint `/auth/logout`

#### Antes:
```
"Error cerrando sesión: {error_técnico}"
```

#### Después:
```
"Error al cerrar sesión. Por favor, intenta nuevamente."
```
- Status: 400 Bad Request
- Sin detalles técnicos

### Endpoint `/auth/callback`

#### Antes:
```
"Error intercambiando código por token: {error_técnico}"
```

#### Después:
```
"Código de autorización inválido o expirado. Por favor, intenta iniciar sesión nuevamente."
```
- Status: 400 Bad Request
- Explica qué hacer a continuación

### Endpoint `/auth/create-user`

#### Antes:
```
"Servicio de autenticación no disponible. Verifica que Keycloak esté corriendo."
```

#### Después:
```
"Servicio de autenticación no disponible. Por favor, intenta más tarde."
```
- Status: 503 Service Unavailable
- Sin mencionar Keycloak

## Mejoras de Seguridad

### Validación en Dos Pasos
El endpoint de login ahora valida en dos pasos:

1. **Verificación en BD local**:
   - Verifica si el usuario existe
   - Verifica si está activo
   - Proporciona mensajes específicos

2. **Autenticación en Keycloak**:
   - Solo si el usuario existe y está activo
   - Captura errores específicos de autenticación
   - Proporciona mensajes claros

### Manejo de Excepciones Específicas
Se importa y maneja `KeycloakAuthenticationError` específicamente:
```python
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakError
```

Esto permite diferenciar entre:
- Error de autenticación (contraseña incorrecta)
- Otros errores de Keycloak
- Errores genéricos

## Experiencia de Usuario

### Antes:
```
❌ "Credenciales inválidas"
```
- No queda claro qué está mal
- Usuario no sabe si es el email o la contraseña

### Después:
```
✅ "No existe ningún usuario con esas credenciales."
✅ "La contraseña ingresada es incorrecta."
✅ "Tu cuenta ha sido desactivada. Contacta al coordinador."
```
- Mensajes claros y específicos
- Usuario sabe exactamente qué hacer
- Tono amigable y profesional

## Consideraciones de Seguridad

### Información Revelada
Los nuevos mensajes revelan si un email existe en el sistema. Esto es un trade-off entre:

**Ventajas**:
- Mejor experiencia de usuario
- Mensajes más útiles y accionables
- Reduce frustración

**Desventajas**:
- Permite enumerar emails válidos
- Potencial vector de ataque

**Mitigación**:
- Rate limiting ya implementado (20 intentos/minuto)
- reCAPTCHA habilitado
- Logs de intentos fallidos
- Monitoreo de patrones sospechosos

### Recomendaciones
Si la seguridad es crítica, considerar:
1. Usar mensaje genérico para usuario inexistente y contraseña incorrecta
2. Implementar CAPTCHA después de X intentos fallidos
3. Bloqueo temporal de IP después de Y intentos
4. Notificación al usuario de intentos fallidos

## Testing

### Casos de Prueba

1. **Login exitoso**:
   - Email: `estudiante@internado-uv.cl`
   - Password: `estudiante123`
   - Resultado: ✅ Login exitoso

2. **Usuario no existe**:
   - Email: `noexiste@internado-uv.cl`
   - Password: `cualquiera`
   - Resultado: ❌ "No existe ningún usuario con esas credenciales."

3. **Contraseña incorrecta**:
   - Email: `estudiante@internado-uv.cl`
   - Password: `incorrecta`
   - Resultado: ❌ "La contraseña ingresada es incorrecta."

4. **Cuenta desactivada**:
   - Email de usuario desactivado
   - Password correcta
   - Resultado: ❌ "Tu cuenta ha sido desactivada. Contacta al coordinador."

5. **Keycloak no disponible**:
   - Detener Keycloak
   - Intentar login
   - Resultado: ❌ "Servicio de autenticación no disponible. Por favor, intenta más tarde."

## Impacto en Frontend

El frontend ya maneja estos errores correctamente:
```javascript
catch (err) {
  const errorMessage = err.response?.data?.detail || 'Error al iniciar sesión'
  setError(errorMessage)
}
```

Los nuevos mensajes se mostrarán automáticamente en la UI sin cambios necesarios.

## Logs

Los logs internos siguen siendo técnicos y detallados:
```python
logger.error(f"Error en login: {e}")
logger.warning(f"Usuario {email} no encontrado")
```

Solo los mensajes al usuario son simplificados.
