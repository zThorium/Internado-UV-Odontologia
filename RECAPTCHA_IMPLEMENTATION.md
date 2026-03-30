# Implementación de reCAPTCHA v2 en Login

## Resumen

Se ha implementado reCAPTCHA v2 de Google en el formulario de login para proteger contra bots y ataques automatizados.

## Claves de reCAPTCHA

- **Site Key (Frontend)**: `6Ldh5pksAAAAAN1daWsi6zKicrHUU8QdzLL9cdPo`
- **Secret Key (Backend)**: `6Ldh5pksAAAAAMF8OQwyLQi00Q126kxh50iDN_IN`

## Cambios Realizados

### Backend

1. **Configuración** (`backend/app/core/config.py`)
   - Agregadas variables `RECAPTCHA_SECRET_KEY` y `RECAPTCHA_ENABLED`

2. **Servicio de Validación** (`backend/app/services/recaptcha.py`)
   - Nuevo servicio `verify_recaptcha()` que valida tokens con la API de Google
   - Implementa fail-open en caso de error de red (permite login si Google no responde)

3. **Schema de Login** (`backend/app/schemas/auth.py`)
   - Agregado campo opcional `recaptcha_token` al `LoginRequest`

4. **Endpoint de Login** (`backend/app/routers/auth.py`)
   - Validación de reCAPTCHA antes de autenticar con Keycloak
   - Retorna error 400 si el captcha falla

5. **Variables de Entorno**
   - Actualizados `backend/.env` y `backend/.env.example` con las claves

### Frontend

1. **LoginPage** (`frontend/src/pages/LoginPage.jsx`)
   - Carga dinámica del script de reCAPTCHA
   - Renderizado del widget de reCAPTCHA
   - Obtención y envío del token al backend
   - Reset del captcha en caso de error
   - Deshabilita el botón de login hasta que reCAPTCHA esté cargado

2. **AuthContext** (`frontend/src/context/AuthContext.jsx`)
   - Actualizada función `login()` para aceptar y enviar `recaptchaToken`

## Cómo Funciona

1. El usuario accede a la página de login
2. Se carga el script de reCAPTCHA desde Google
3. Se renderiza el widget "No soy un robot"
4. El usuario completa sus credenciales y marca el checkbox
5. Al enviar el formulario:
   - Se obtiene el token de respuesta de reCAPTCHA
   - Se envía junto con email y password al backend
6. El backend valida el token con Google
7. Si es válido, procede con la autenticación en Keycloak
8. Si falla, retorna error y el captcha se resetea

## Configuración

### Habilitar/Deshabilitar reCAPTCHA

En `backend/.env`:

```env
# Habilitar
RECAPTCHA_ENABLED=true

# Deshabilitar (útil para desarrollo)
RECAPTCHA_ENABLED=false
```

### Dominios Autorizados

Asegúrate de que tu dominio esté registrado en la consola de Google reCAPTCHA:
- Desarrollo: `localhost`
- Producción: tu dominio real

## Testing

### Modo de Prueba

Para testing automatizado, puedes:

1. Deshabilitar reCAPTCHA temporalmente:
   ```env
   RECAPTCHA_ENABLED=false
   ```

2. O usar las claves de prueba de Google:
   - Site Key: `6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI`
   - Secret Key: `6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe`
   
   Estas claves siempre retornan éxito.

### Probar Manualmente

1. Inicia el backend: `cd backend && uvicorn app.main:app --reload`
2. Inicia el frontend: `cd frontend && npm run dev`
3. Accede a `http://localhost:5173/login`
4. Completa el formulario y marca el checkbox de reCAPTCHA
5. Intenta hacer login

## Seguridad

- El token de reCAPTCHA es de un solo uso
- Se valida en el servidor (no confiar solo en el frontend)
- La IP del cliente se envía a Google para mejor detección
- En caso de error de red con Google, el sistema permite el login (fail-open)
  - En producción podrías cambiar a fail-closed editando `recaptcha.py`

## Troubleshooting

### El widget no aparece
- Verifica que el script se cargue correctamente (revisa la consola del navegador)
- Confirma que la Site Key sea correcta

### Error "Validación de reCAPTCHA fallida"
- Verifica que la Secret Key en el backend sea correcta
- Confirma que el dominio esté autorizado en Google reCAPTCHA
- Revisa los logs del backend para más detalles

### Error de red
- Si Google reCAPTCHA no responde, el sistema permite el login por defecto
- Revisa la conectividad del servidor backend con `https://www.google.com`

## Próximos Pasos

- Monitorear métricas de reCAPTCHA en la consola de Google
- Ajustar el umbral de seguridad si es necesario
- Considerar migrar a reCAPTCHA v3 (invisible) en el futuro
