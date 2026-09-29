"""Endpoint principal de verificación de identidad.

Recibe una selfie en vivo para una persona ya registrada, la compara
contra su embedding de referencia y decide si el acceso se concede o se
deniega. Si se concede, clasifica el evento como entrada o salida
(alternando según el último registro de esa persona), actualiza su
estado de asistencia y envía el correo de confirmación correspondiente.
"""
import json
from datetime import datetime

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import email_service, face_service
from ..database import get_db
from ..models import EventoVerificacion, Persona
from ..schemas import VerificacionOut

router = APIRouter(prefix="/verificar", tags=["verificacion"])


@router.post("", response_model=VerificacionOut)
async def verificar_identidad(
    persona_id: int = Form(...),
    selfie: UploadFile = File(..., description="Foto capturada en vivo"),
    db: Session = Depends(get_db),
):
    persona = db.get(Persona, persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")

    if persona.embedding_backend != face_service.get_backend_name():
        raise HTTPException(
            status_code=409,
            detail=(
                "La persona fue registrada con un motor de reconocimiento distinto al activo "
                f"({persona.embedding_backend} vs {face_service.get_backend_name()}). "
                "Debe volver a registrarse."
            ),
        )

    image_bytes = await selfie.read()
    try:
        probe_embedding = face_service.extract_embedding(image_bytes)
    except face_service.NoFaceDetectedError:
        raise HTTPException(status_code=422, detail="No se detectó un rostro en la selfie.")

    ref_embedding = np.array(json.loads(persona.embedding_json), dtype="float32")
    match = face_service.compare_embeddings(ref_embedding, probe_embedding)

    tipo_evento = "salida" if persona.ultimo_tipo_evento == "entrada" else "entrada"
    resultado = "concedido" if match.is_match else "denegado"
    tipo_registrado = tipo_evento if match.is_match else "rechazado"

    evento = EventoVerificacion(
        persona_id=persona.id,
        tipo=tipo_registrado,
        resultado=resultado,
        score=match.score,
    )
    db.add(evento)

    mensaje = "Acceso denegado: el rostro no coincide con el registrado."
    if match.is_match:
        persona.ultimo_tipo_evento = tipo_evento
        if tipo_evento == "entrada":
            # Nueva entrada: reinicia la ventana móvil de 24h de asistencia.
            persona.ultima_entrada_en = datetime.utcnow()
            persona.aviso_previo_enviado = False
            persona.aviso_final_enviado = False

        email_service.enviar_confirmacion_evento(
            persona.email,
            persona.nombre,
            tipo_evento,
            datetime.utcnow().strftime("%d-%m-%Y %H:%M"),
        )
        mensaje = f"{tipo_evento.capitalize()} registrada correctamente."

    db.commit()

    return VerificacionOut(
        persona_id=persona.id,
        nombre=persona.nombre,
        tipo_evento=tipo_registrado,
        resultado=resultado,
        score=match.score,
        mensaje=mensaje,
    )
