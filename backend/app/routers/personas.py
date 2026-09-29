"""Endpoints de registro de personas.

Registrar a una persona implica subir una foto de referencia (normalmente
la foto del documento de identidad); el backend extrae su embedding
facial y lo guarda para comparar contra las selfies capturadas en cada
verificación posterior.
"""
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import face_service
from ..database import get_db
from ..models import Persona
from ..schemas import PersonaOut

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("", response_model=PersonaOut, status_code=201)
async def registrar_persona(
    nombre: str = Form(...),
    email: str = Form(...),
    foto: UploadFile = File(..., description="Foto de referencia (ej. del documento de identidad)"),
    db: Session = Depends(get_db),
):
    existente = db.query(Persona).filter(Persona.email == email).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe una persona registrada con ese correo.")

    image_bytes = await foto.read()
    try:
        embedding = face_service.extract_embedding(image_bytes)
    except face_service.NoFaceDetectedError:
        raise HTTPException(status_code=422, detail="No se detectó un rostro en la foto de referencia.")

    persona = Persona(
        nombre=nombre,
        email=email,
        embedding_json=json.dumps(embedding.tolist()),
        embedding_backend=face_service.get_backend_name(),
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


@router.get("", response_model=list[PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    return db.query(Persona).order_by(Persona.nombre).all()


@router.get("/{persona_id}", response_model=PersonaOut)
def obtener_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.get(Persona, persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada.")
    return persona
