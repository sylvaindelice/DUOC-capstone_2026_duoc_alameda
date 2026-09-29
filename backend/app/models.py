"""Modelos SQLAlchemy: Persona y EventoVerificacion.

Persona guarda el embedding facial de referencia (extraído de la foto de
su documento de identidad al momento de registrarse) y el estado de su
control de asistencia (ventana móvil de 24 horas, ver app/attendance.py).

EventoVerificacion es el registro histórico de cada intento de
verificación (entrada, salida o rechazo), usado tanto para auditoría
como para el panel de resultados.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(180), nullable=False, unique=True, index=True)

    # Representación facial de referencia, serializada como JSON (lista de floats).
    embedding_json = Column(Text, nullable=False)
    # Motor con el que se generó el embedding ("face_recognition" u "opencv_lbp").
    # Se guarda para no comparar embeddings incompatibles entre sí si el motor
    # activo cambia entre el registro y la verificación.
    embedding_backend = Column(String(30), nullable=False)

    creado_en = Column(DateTime, default=datetime.utcnow)

    # --- Control de asistencia (ventana móvil de 24h) ---
    ultima_entrada_en = Column(DateTime, nullable=True)
    ultimo_tipo_evento = Column(String(10), nullable=True)  # "entrada" | "salida"
    aviso_previo_enviado = Column(Boolean, default=False)
    aviso_final_enviado = Column(Boolean, default=False)

    eventos = relationship(
        "EventoVerificacion", back_populates="persona", order_by="EventoVerificacion.creado_en.desc()"
    )


class EventoVerificacion(Base):
    __tablename__ = "eventos_verificacion"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False)

    tipo = Column(String(10), nullable=False)       # "entrada" | "salida" | "rechazado"
    resultado = Column(String(12), nullable=False)  # "concedido" | "denegado"
    score = Column(Float, nullable=False)

    creado_en = Column(DateTime, default=datetime.utcnow)

    persona = relationship("Persona", back_populates="eventos")
