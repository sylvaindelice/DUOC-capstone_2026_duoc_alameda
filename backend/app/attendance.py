"""Lógica de control de asistencia: ventana móvil de 24 horas por persona.

En vez de comparar contra un horario fijo de oficina (por ejemplo,
08:00–18:00), el sistema calcula, para cada persona, cuántas horas han
pasado desde su último registro de entrada. Así, el mismo mecanismo sirve
para personas con distintos turnos (ej. alguien de 08:00 a 18:00 y alguien
de 09:00 a 20:00 reciben sus avisos igual, calculados desde su propio
último registro). Ver propuesta de proyecto, sección 5.3.

Este módulo es lógica pura (sin base de datos ni framework web) para que
sea fácil de probar de forma aislada — ver tests/test_attendance.py.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

AVISO_PREVIO_HORAS = 20
AVISO_FINAL_HORAS = 24


class ReminderState(str, Enum):
    OK = "ok"                      # dentro de la ventana normal; no se envía nada
    AVISO_PREVIO = "aviso_previo"  # pasaron >= 20h sin nueva entrada
    AVISO_FINAL = "aviso_final"    # pasaron >= 24h sin nueva entrada


@dataclass
class AttendanceCheck:
    state: ReminderState
    hours_since_last_entry: float


def evaluate_attendance(
    last_entry_at: datetime | None,
    now: datetime,
    aviso_previo_horas: float = AVISO_PREVIO_HORAS,
    aviso_final_horas: float = AVISO_FINAL_HORAS,
) -> AttendanceCheck:
    """Determina si corresponde enviar un aviso de asistencia para una persona.

    - Si la persona nunca ha registrado una entrada, se considera OK
      (no aplica todavía el control de asistencia).
    - Si han pasado >= aviso_final_horas desde la última entrada: AVISO_FINAL.
    - Si han pasado >= aviso_previo_horas (pero menos que el final): AVISO_PREVIO.
    - En cualquier otro caso: OK.
    """
    if last_entry_at is None:
        return AttendanceCheck(state=ReminderState.OK, hours_since_last_entry=0.0)

    elapsed = (now - last_entry_at).total_seconds() / 3600
    if elapsed >= aviso_final_horas:
        return AttendanceCheck(state=ReminderState.AVISO_FINAL, hours_since_last_entry=elapsed)
    if elapsed >= aviso_previo_horas:
        return AttendanceCheck(state=ReminderState.AVISO_PREVIO, hours_since_last_entry=elapsed)
    return AttendanceCheck(state=ReminderState.OK, hours_since_last_entry=elapsed)
