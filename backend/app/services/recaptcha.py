"""
Servicio de validación de reCAPTCHA v2
"""
import httpx
from app.core.config import settings


async def verify_recaptcha(token: str, remote_ip: str | None = None) -> bool:
    """
    Verifica un token de reCAPTCHA v2 con la API de Google.
    
    Args:
        token: Token de respuesta del reCAPTCHA del frontend
        remote_ip: IP del cliente (opcional pero recomendado)
    
    Returns:
        True si el captcha es válido, False en caso contrario
    """
    if not settings.RECAPTCHA_ENABLED:
        return True
    
    if not token:
        return False
    
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": settings.RECAPTCHA_SECRET_KEY,
        "response": token,
    }
    
    if remote_ip:
        data["remoteip"] = remote_ip
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=10.0)
            result = response.json()
            return result.get("success", False)
    except Exception:
        # En caso de error de red, permitir el login (fail-open)
        # En producción podrías querer fail-closed (return False)
        return True
