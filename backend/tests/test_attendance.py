"""Pruebas de la lógica de control de asistencia (ventana móvil de 24h).

Esta es la lógica que responde a la pregunta del profesor sobre personas
con distintos turnos: no se compara contra un horario fijo, sino contra
las horas transcurridas desde el último registro de entrada de cada
persona (ver app/attendance.py y la propuesta, sección 5.3).
"""
from datetime import datetime, timedelta

from app.attendance import ReminderState, evaluate_attendance


def test_sin_entrada_previa_no_genera_aviso():
    check = evaluate_attendance(last_entry_at=None, now=datetime(2026, 1, 1, 12, 0))
    assert check.state == ReminderState.OK


def test_dentro_de_la_ventana_normal_no_genera_aviso():
    entrada = datetime(2026, 1, 1, 8, 0)
    ahora = entrada + timedelta(hours=10)
    check = evaluate_attendance(entrada, ahora)
    assert check.state == ReminderState.OK


def test_a_las_20_horas_genera_aviso_previo():
    entrada = datetime(2026, 1, 1, 8, 0)
    ahora = entrada + timedelta(hours=20)
    check = evaluate_attendance(entrada, ahora)
    assert check.state == ReminderState.AVISO_PREVIO


def test_a_las_24_horas_genera_aviso_final():
    entrada = datetime(2026, 1, 1, 8, 0)
    ahora = entrada + timedelta(hours=24)
    check = evaluate_attendance(entrada, ahora)
    assert check.state == ReminderState.AVISO_FINAL


def test_funciona_igual_sin_importar_el_turno_de_la_persona():
    """La pregunta concreta del profesor: alguien con turno 09:00-20:00 debe
    recibir los mismos avisos (a las +20h y +24h desde SU última entrada),
    sin depender de un horario de oficina fijo como 08:00-18:00."""
    turno_manana = datetime(2026, 1, 1, 8, 0)
    turno_tarde = datetime(2026, 1, 1, 9, 0)  # persona con turno 09:00-20:00

    check_manana = evaluate_attendance(turno_manana, turno_manana + timedelta(hours=20))
    check_tarde = evaluate_attendance(turno_tarde, turno_tarde + timedelta(hours=20))

    assert check_manana.state == ReminderState.AVISO_PREVIO
    assert check_tarde.state == ReminderState.AVISO_PREVIO


def test_umbrales_configurables():
    entrada = datetime(2026, 1, 1, 8, 0)
    ahora = entrada + timedelta(hours=5)
    check = evaluate_attendance(entrada, ahora, aviso_previo_horas=4, aviso_final_horas=6)
    assert check.state == ReminderState.AVISO_PREVIO
