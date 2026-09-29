"""Esquemas Pydantic para validar entradas y dar forma a las respuestas de la API."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class PersonaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    creado_en: datetime
    ultima_entrada_en: datetime | None = None
    ultimo_tipo_evento: str | None = None


class VerificacionOut(BaseModel):
    persona_id: int
    nombre: str
    tipo_evento: str
    resultado: str
    score: float
    mensaje: str


class EventoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    persona_id: int
    tipo: str
    resultado: str
    score: float
    creado_en: datetime
