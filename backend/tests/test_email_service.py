"""Pruebas del servicio de correo. Con APP_SMTP_ENABLED=False (valor por
defecto en pruebas), los correos no se envían de verdad: solo se registran
en el log, lo que permite probar el flujo completo sin credenciales SMTP."""
from app import email_service


def test_confirmacion_evento_no_falla_sin_smtp_configurado():
    ok = email_service.enviar_confirmacion_evento(
        "persona@example.com", "Ana Pérez", "entrada", "08-09-2026 09:15"
    )
    assert ok is True


def test_aviso_previo_no_falla_sin_smtp_configurado():
    assert email_service.enviar_aviso_previo("persona@example.com", "Ana Pérez") is True


def test_aviso_final_no_falla_sin_smtp_configurado():
    assert email_service.enviar_aviso_final("persona@example.com", "Ana Pérez") is True


def test_envio_real_usa_smtplib_y_reporta_error_si_falla(monkeypatch):
    """Si se activa el envío real (APP_SMTP_ENABLED=True) y el servidor SMTP
    falla, la función debe devolver False en vez de lanzar una excepción."""
    from app.config import settings

    monkeypatch.setattr(settings, "smtp_enabled", True)
    monkeypatch.setattr(settings, "smtp_host", "smtp.invalido.local")
    monkeypatch.setattr(settings, "smtp_port", 1)

    ok = email_service.enviar_confirmacion_evento(
        "persona@example.com", "Ana Pérez", "salida", "08-09-2026 18:05"
    )
    assert ok is False
