import logging

logger = logging.getLogger(__name__)


async def send_incident_notification(student_id: str, incident_type: str) -> None:
    """
    Notifica sobre un nuevo incidente reportado.
    En desarrollo: solo loguea (no envía email real).
    """
    logger.info("Incident notification: student=%s type=%s", student_id, incident_type)


async def send_reset_password_email(email: str, reset_token: str) -> None:
    """
    Envía email con link de reset de contraseña.
    En desarrollo: solo loguea el token (no envía email real).
    En producción: usar fastapi-mail.
    """
    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
    logger.info(
        "Reset password requested for %s — link: %s",
        email,
        reset_link,
    )


async def send_welcome_email(email: str, full_name: str) -> None:
    """
    Envía email de bienvenida a un nuevo tutor.
    En desarrollo: solo loguea (no envía email real).
    """
    logger.info("Welcome email sent to %s (%s)", email, full_name)
