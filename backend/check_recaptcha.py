#!/usr/bin/env python3
"""
Script para verificar el estado de la configuración de reCAPTCHA
"""
import sys
sys.path.insert(0, '.')

from app.core.config import settings

print("=" * 60)
print("VERIFICACIÓN DE CONFIGURACIÓN DE reCAPTCHA")
print("=" * 60)
print()
print(f"RECAPTCHA_ENABLED: {settings.RECAPTCHA_ENABLED}")
print(f"RECAPTCHA_SECRET_KEY: {settings.RECAPTCHA_SECRET_KEY[:20]}...")
print()

if settings.RECAPTCHA_ENABLED:
    print("⚠️  reCAPTCHA está ACTIVADO")
    print("   El login requiere resolver el captcha")
    print()
    print("Para desactivar:")
    print("1. Edita backend/app/core/config.py")
    print("2. Cambia RECAPTCHA_ENABLED: bool = False")
    print("3. Reinicia el backend")
else:
    print("✅ reCAPTCHA está DESACTIVADO")
    print("   El login NO requiere resolver el captcha")
    print()
    print("Para activar en producción:")
    print("1. Edita backend/app/core/config.py")
    print("2. Cambia RECAPTCHA_ENABLED: bool = True")
    print("3. Reinicia el backend")

print()
print("=" * 60)
