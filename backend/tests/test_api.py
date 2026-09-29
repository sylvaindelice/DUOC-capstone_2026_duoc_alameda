"""Pruebas de integración de la API HTTP (endpoints de FastAPI).

Requieren fastapi y sqlalchemy instalados (ver requirements.txt). Si no
están disponibles, estas pruebas se omiten automáticamente (skip) en vez
de fallar — así el resto de la suite (face_service, attendance,
email_service, que no dependen de FastAPI) se puede seguir ejecutando en
cualquier entorno.
"""
import os
import tempfile

import pytest

# Base de datos aislada para las pruebas (un archivo temporal por sesión de
# pytest), configurada antes de importar la app para que app/database.py
# la use al crear el engine.
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.setdefault("APP_DATABASE_URL", f"sqlite:///{_db_file.name}")
os.environ.setdefault("APP_SMTP_ENABLED", "False")

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_salud():
    resp = client.get("/salud")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_flujo_completo_registro_entrada_salida(foto_referencia_bytes, foto_misma_persona_bytes):
    # 1. Registrar persona con su foto de referencia (documento de identidad)
    resp = client.post(
        "/personas",
        data={"nombre": "Ana Pérez", "email": "ana@example.com"},
        files={"foto": ("foto.png", foto_referencia_bytes, "image/png")},
    )
    assert resp.status_code == 201
    persona_id = resp.json()["id"]

    # 2. Primera verificación exitosa -> debe registrarse como ENTRADA
    resp = client.post(
        "/verificar",
        data={"persona_id": persona_id},
        files={"selfie": ("selfie.png", foto_misma_persona_bytes, "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["resultado"] == "concedido"
    assert body["tipo_evento"] == "entrada"

    # 3. Segunda verificación exitosa -> debe alternar a SALIDA
    resp = client.post(
        "/verificar",
        data={"persona_id": persona_id},
        files={"selfie": ("selfie.png", foto_misma_persona_bytes, "image/png")},
    )
    assert resp.status_code == 200
    assert resp.json()["tipo_evento"] == "salida"

    # 4. El historial debe tener 2 eventos registrados para esta persona
    resp = client.get("/eventos", params={"persona_id": persona_id})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_verificar_persona_inexistente_devuelve_404(foto_referencia_bytes):
    resp = client.post(
        "/verificar",
        data={"persona_id": 999999},
        files={"selfie": ("selfie.png", foto_referencia_bytes, "image/png")},
    )
    assert resp.status_code == 404


def test_registrar_correo_duplicado_devuelve_409(foto_referencia_bytes):
    client.post(
        "/personas",
        data={"nombre": "Persona Uno", "email": "duplicado@example.com"},
        files={"foto": ("foto.png", foto_referencia_bytes, "image/png")},
    )
    resp = client.post(
        "/personas",
        data={"nombre": "Persona Dos", "email": "duplicado@example.com"},
        files={"foto": ("foto.png", foto_referencia_bytes, "image/png")},
    )
    assert resp.status_code == 409
