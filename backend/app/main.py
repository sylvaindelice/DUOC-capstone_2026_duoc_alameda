"""Punto de entrada de la aplicación FastAPI.

Ejecutar en desarrollo con:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import face_service
from .database import Base, engine
from .routers import historial, personas, verificacion
from .scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sistema de verificación de identidad",
        description=(
            "API de control de acceso mediante comparación biométrica facial, "
            "con control de asistencia (ventana móvil de 24h) y notificaciones por correo."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(personas.router)
    app.include_router(verificacion.router)
    app.include_router(historial.router)

    @app.get("/salud", tags=["salud"])
    def salud():
        return {"status": "ok", "motor_facial": face_service.get_backend_name()}

    return app


app = create_app()
