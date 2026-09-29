"""Programador de tareas (APScheduler): revisa periódicamente la ventana
móvil de 24 horas de cada persona y envía los correos de recordatorio
correspondientes (ver app/attendance.py y la propuesta, sección 5.3).

Se ejecuta como un job en segundo plano dentro del propio proceso del
backend (BackgroundScheduler), con un intervalo configurable
(APP_SCHEDULER_INTERVAL_MINUTOS, por defecto cada 60 minutos).
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from . import email_service
from .attendance import ReminderState, evaluate_attendance
from .config import settings
from .database import SessionLocal
from .models import Persona

logger = logging.getLogger(__name__)


def revisar_asistencia() -> None:
    """Job del scheduler: recorre las personas con al menos una entrada registrada
    y envía aviso previo o aviso final según corresponda, evitando reenviar el
    mismo aviso más de una vez por ausencia."""
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        personas = db.query(Persona).filter(Persona.ultima_entrada_en.isnot(None)).all()
        for persona in personas:
            check = evaluate_attendance(
                persona.ultima_entrada_en,
                now,
                aviso_previo_horas=settings.aviso_previo_horas,
                aviso_final_horas=settings.aviso_final_horas,
            )
            if check.state == ReminderState.AVISO_PREVIO and not persona.aviso_previo_enviado:
                email_service.enviar_aviso_previo(persona.email, persona.nombre)
                persona.aviso_previo_enviado = True
            elif check.state == ReminderState.AVISO_FINAL and not persona.aviso_final_enviado:
                email_service.enviar_aviso_final(persona.email, persona.nombre)
                persona.aviso_final_enviado = True
        db.commit()
    finally:
        db.close()


_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        revisar_asistencia,
        "interval",
        minutes=settings.scheduler_interval_minutos,
        id="revisar_asistencia",
        next_run_time=datetime.utcnow(),  # corre una vez apenas arranca el servidor
    )
    _scheduler.start()
    logger.info("Scheduler iniciado: revisa asistencia cada %s minutos.", settings.scheduler_interval_minutos)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
