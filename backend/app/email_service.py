"""Envío de notificaciones por correo: confirmación de entrada/salida y
recordatorios de asistencia (aviso previo a las 20h, aviso final a las 24h).

Si APP_SMTP_ENABLED no está activado (valor por defecto), los correos no
se envían de verdad: solo se registran en el log. Esto permite probar todo
el flujo sin necesitar credenciales SMTP reales.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import settings

logger = logging.getLogger(__name__)


def _send(to_email: str, subject: str, body: str) -> bool:
    if not settings.smtp_enabled:
        logger.info("[EMAIL simulado] Para: %s | Asunto: %s\n%s", to_email, subject, body)
        return True

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        return True
    except Exception:
        logger.exception("No se pudo enviar el correo a %s", to_email)
        return False


def enviar_confirmacion_evento(to_email: str, nombre: str, tipo_evento: str, hora_texto: str) -> bool:
    subject = f"Confirmación de {tipo_evento} registrada"
    body = (
        f"Hola {nombre},\n\n"
        f"Se registró tu {tipo_evento} el {hora_texto}.\n\n"
        "Si no reconoces este evento, contacta al administrador del sistema.\n"
    )
    return _send(to_email, subject, body)


def enviar_aviso_previo(to_email: str, nombre: str) -> bool:
    subject = "Recordatorio: aún no registras tu entrada"
    body = (
        f"Hola {nombre},\n\n"
        "Han pasado 20 horas desde tu último registro de entrada y todavía no "
        "marcas una nueva entrada. Recuerda hacerlo a través de la app.\n"
    )
    return _send(to_email, subject, body)


def enviar_aviso_final(to_email: str, nombre: str) -> bool:
    subject = "Aviso de inasistencia"
    body = (
        f"Hola {nombre},\n\n"
        "Han pasado 24 horas desde tu último registro de entrada sin un nuevo "
        "registro. Este es un aviso automático de inasistencia.\n"
    )
    return _send(to_email, subject, body)
