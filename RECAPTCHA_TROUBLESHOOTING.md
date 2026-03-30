# Troubleshooting: reCAPTCHA sigue activo

## Problema
Ves el error: "Verificación de seguridad fallida. Por favor, intenta nuevamente."

## Causa
El backend no ha recargado la configuración después de cambiar `RECAPTCHA_ENABLED = False`

## Solución Rápida

### Paso 1: Detener el Backend
En la terminal donde está corriendo el backend, presiona:
```
Ctrl + C
```

### Paso 2: Verificar el Cambio
Abre `backend/app/core/config.py` y verifica la línea 70:
```python
RECAPTCHA_ENABLED: bool = False  # ⚠️ Debe estar en False
```

### Paso 3: Reiniciar el Backend
```bash
cd backend
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 4: Verificar en los Logs
Cuando el backend inicie, deberías ver algo como:
```
INFO: Application startup complete.
```

### Paso 5: Probar el Login
Ahora intenta hacer login nuevamente. Debería funcionar sin el captcha.

## Verificación Adicional

### Opción 1: Usar Variable de Entorno (Recomendado)

Crea o edita `backend/.env`:
```bash
RECAPTCHA_ENABLED=false
```

Luego reinicia el backend.

### Opción 2: Verificar que el Cambio se Aplicó

Puedes agregar un log temporal en `backend/app/routers/auth.py` línea 40:

```python
# Validar reCAPTCHA si está habilitado
print(f"[DEBUG] RECAPTCHA_ENABLED = {settings.RECAPTCHA_ENABLED}")  # ← Agregar esta línea
if settings.RECAPTCHA_ENABLED:
    client_ip = request.client.host if request.client else None
    is_valid = await verify_recaptcha(credentials.recaptcha_token, client_ip)
    ...
```

Reinicia el backend y verifica en los logs que diga:
```
[DEBUG] RECAPTCHA_ENABLED = False
```

## Si Sigue Sin Funcionar

### 1. Verifica que estás editando el archivo correcto
```bash
# Desde la raíz del proyecto
cat backend/app/core/config.py | grep RECAPTCHA_ENABLED
```

Debería mostrar:
```python
RECAPTCHA_ENABLED: bool = False
```

### 2. Verifica que el backend esté usando el archivo correcto
```bash
# En la terminal del backend, verifica la ruta
pwd
# Debería mostrar algo como: /ruta/a/tu/proyecto/backend
```

### 3. Limpia el caché de Python
```bash
cd backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

Luego reinicia el backend.

### 4. Usa el script de desarrollo
Si tienes el script `dev.sh`:
```bash
./dev.sh restart backend
```

## Comandos Útiles

### Ver logs del backend en tiempo real
```bash
# Si usas dev.sh
./dev.sh logs backend

# Si usas uvicorn directamente
# Los logs aparecen en la misma terminal
```

### Verificar que el puerto 8000 esté libre
```bash
# macOS/Linux
lsof -i :8000

# Si hay algo corriendo, mátalo
kill -9 <PID>
```

### Reinicio completo
```bash
# Detener todo
./dev.sh stop

# Iniciar solo lo necesario
./dev.sh start db keycloak
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Verificación Final

Una vez reiniciado el backend, haz una prueba:

1. Abre el frontend: http://localhost:5173
2. Intenta hacer login con:
   - Email: `estudiante@internado-uv.cl`
   - Password: `estudiante123`
3. **NO** hagas clic en el captcha
4. Haz clic en "Ingresar"
5. Debería funcionar sin error

## Si Todo Falla

Como última opción, puedes comentar completamente la validación de reCAPTCHA:

**Archivo**: `backend/app/routers/auth.py` (líneas 40-50)

```python
# Validar reCAPTCHA si está habilitado
# TEMPORALMENTE DESACTIVADO PARA DESARROLLO
"""
if settings.RECAPTCHA_ENABLED:
    client_ip = request.client.host if request.client else None
    is_valid = await verify_recaptcha(credentials.recaptcha_token, client_ip)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validación de reCAPTCHA fallida. Por favor, intenta nuevamente.",
        )
"""
```

**IMPORTANTE**: Recuerda descomentar esto antes de ir a producción.

## Contacto

Si ninguna de estas soluciones funciona, comparte:
1. El contenido de `backend/app/core/config.py` (líneas 67-72)
2. Los logs completos del backend al iniciar
3. El error exacto que ves en el frontend
