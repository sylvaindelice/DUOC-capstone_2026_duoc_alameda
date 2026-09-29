"""Configuración centralizada de la aplicación.

Todos los valores pueden sobrescribirse mediante variables de entorno con
el prefijo APP_ (por ejemplo APP_SMTP_HOST) o mediante un archivo .env en
la raíz de backend/. Ver .env.example.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    # Base de datos
    database_url: str = "sqlite:///./identidad.db"

    # Reconocimiento facial
    # None = usa el umbral por defecto del backend activo (ver app/face_service.py)
    face_match_threshold: float | None = None





    @field_validator("face_match_threshold", mode="before")
    @classmethod
    def _vacio_es_none(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v
    # Control de asistencia — ventana móvil de 24 horas por persona
    # (ver propuesta de proyecto, sección 5.3: no se usa un horario fijo
    # de oficina porque distintas personas pueden tener distintos turnos).
    aviso_previo_horas: float = 20
    aviso_final_horas: float = 24
    scheduler_interval_minutos: int = 60

    # Envío de correo (SMTP)
    smtp_enabled: bool = False  # si es False, los correos solo se registran en el log
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@identidad-app.local"


settings = Settings()
