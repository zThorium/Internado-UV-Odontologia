# Configuración de reCAPTCHA

## Estado Actual
🔴 **DESACTIVADO** - Para facilitar el desarrollo

## Cómo Activar reCAPTCHA para Producción

### Paso 1: Backend - Activar en Configuración

**Archivo**: `backend/app/core/config.py`

```python
# Línea 67-70
RECAPTCHA_SECRET_KEY: str = "6Ldh5pksAAAAAMF8OQwyLQi00Q126kxh50iDN_IN"
RECAPTCHA_ENABLED: bool = True  # ⚠️ Cambiar de False a True
```

**O usando variable de entorno** (recomendado para producción):

**Archivo**: `backend/.env`

```bash
RECAPTCHA_ENABLED=true
RECAPTCHA_SECRET_KEY=6Ldh5pksAAAAAMF8OQwyLQi00Q126kxh50iDN_IN
```

### Paso 2: Verificar que el Frontend esté Configurado

El frontend ya está configurado correctamente. El componente reCAPTCHA se muestra automáticamente en el login.

**Archivo**: `frontend/src/pages/LoginPage.jsx`

El código ya incluye:
```javascript
<ReCAPTCHA
  sitekey="6Ldh5pksAAAAAN1daWsi6zKicrHUU8QdzLL9cdPo"
  onChange={handleRecaptchaChange}
  theme="light"
/>
```

### Paso 3: Reiniciar el Backend

Después de cambiar la configuración:

```bash
# Detener el backend (Ctrl+C)
# Reiniciar
cd backend
source .venv/bin/activate  # o .venv\Scripts\activate en Windows
uvicorn app.main:app --reload
```

## Cómo Funciona

### Cuando está DESACTIVADO (desarrollo)
- ✅ El widget de reCAPTCHA se muestra en el frontend (opcional)
- ✅ El usuario puede hacer clic en "No soy un robot" o ignorarlo
- ✅ El backend **NO valida** el token de reCAPTCHA
- ✅ El login funciona **sin necesidad** de resolver el captcha
- ✅ El botón "Ingresar" está siempre habilitado

### Cuando está ACTIVADO (producción)
- ✅ El widget de reCAPTCHA se muestra en el frontend
- ✅ El usuario debe hacer clic en "No soy un robot"
- ✅ El backend **SÍ valida** el token con Google reCAPTCHA API
- ❌ Si el captcha es inválido, el login falla con error
- ⚠️ El botón "Ingresar" solo se habilita cuando el captcha está cargado

## Verificar el Estado Actual

### Backend
Puedes verificar si está activado revisando los logs al iniciar el backend:

```bash
# Si ves esto en los logs, está desactivado:
INFO: reCAPTCHA validation: DISABLED (development mode)

# Si ves esto, está activado:
INFO: reCAPTCHA validation: ENABLED
```

### Código del Endpoint de Login

**Archivo**: `backend/app/routers/auth.py` (líneas 40-50)

```python
# Validar reCAPTCHA si está habilitado
if settings.RECAPTCHA_ENABLED:
    client_ip = request.client.host if request.client else None
    is_valid = await verify_recaptcha(credentials.recaptcha_token, client_ip)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validación de reCAPTCHA fallida. Por favor, intenta nuevamente.",
        )
```

## Credenciales de reCAPTCHA

### Site Key (Frontend)
```
6Ldh5pksAAAAAN1daWsi6zKicrHUU8QdzLL9cdPo
```

### Secret Key (Backend)
```
6Ldh5pksAAAAAMF8OQwyLQi00Q126kxh50iDN_IN
```

⚠️ **IMPORTANTE**: Estas son claves de prueba. Para producción, debes:
1. Ir a [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Crear un nuevo sitio con tu dominio de producción
3. Obtener nuevas claves (Site Key y Secret Key)
4. Actualizar las claves en el código

## Configuración por Entorno

### Desarrollo (Local)
```bash
# backend/.env
RECAPTCHA_ENABLED=false
```

### Staging (Pruebas)
```bash
# backend/.env
RECAPTCHA_ENABLED=true
RECAPTCHA_SECRET_KEY=tu_secret_key_de_staging
```

### Producción
```bash
# backend/.env.prod
RECAPTCHA_ENABLED=true
RECAPTCHA_SECRET_KEY=tu_secret_key_de_produccion
```

## Troubleshooting

### Problema: "ERROR del propietario del sitio: El tipo de clave no es válido"

**Causa**: Las claves de reCAPTCHA no coinciden o son inválidas.

**Solución**:
1. Verifica que la Site Key en el frontend coincida con la registrada en Google
2. Verifica que la Secret Key en el backend coincida con la registrada en Google
3. Asegúrate de usar claves de reCAPTCHA v2 (no v3)

### Problema: El captcha no se muestra

**Causa**: Problema de red o claves incorrectas.

**Solución**:
1. Verifica la conexión a internet
2. Revisa la consola del navegador para errores
3. Verifica que la Site Key sea correcta

### Problema: "Validación de reCAPTCHA fallida"

**Causa**: El token de reCAPTCHA es inválido o expiró.

**Solución**:
1. Intenta hacer login nuevamente
2. Verifica que el backend tenga la Secret Key correcta
3. Revisa los logs del backend para más detalles

## Testing

### Test Manual con reCAPTCHA Desactivado
```bash
# 1. Asegúrate de que RECAPTCHA_ENABLED=false
# 2. Inicia el backend
# 3. Intenta hacer login
# 4. Debería funcionar sin validar el captcha
```

### Test Manual con reCAPTCHA Activado
```bash
# 1. Cambia RECAPTCHA_ENABLED=true
# 2. Reinicia el backend
# 3. Intenta hacer login sin resolver el captcha
# 4. Debería fallar con error de validación
# 5. Resuelve el captcha e intenta de nuevo
# 6. Debería funcionar correctamente
```

## Checklist para Producción

Antes de desplegar a producción:

- [ ] Crear nuevas claves de reCAPTCHA para el dominio de producción
- [ ] Actualizar `RECAPTCHA_SECRET_KEY` en el backend
- [ ] Actualizar `sitekey` en `LoginPage.jsx`
- [ ] Cambiar `RECAPTCHA_ENABLED=true` en el backend
- [ ] Probar el login en el entorno de staging
- [ ] Verificar que el captcha se valide correctamente
- [ ] Monitorear logs para errores de validación
- [ ] Configurar alertas para fallos de reCAPTCHA

## Monitoreo

### Métricas a Monitorear
- Tasa de fallos de validación de reCAPTCHA
- Tiempo de respuesta de la API de Google
- Intentos de login con captcha inválido

### Logs Importantes
```python
# Backend logs
INFO: reCAPTCHA validation successful for IP: 192.168.1.1
WARNING: reCAPTCHA validation failed for IP: 192.168.1.1
ERROR: reCAPTCHA API error: timeout
```

## Referencias

- [Google reCAPTCHA Documentation](https://developers.google.com/recaptcha/docs/display)
- [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
- [Best Practices](https://developers.google.com/recaptcha/docs/faq)
