"""Endpoint de consulta del historial de verificaciones (panel de resultados)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EventoVerificacion
from ..schemas import EventoOut

router = APIRouter(prefix="/eventos", tags=["historial"])


@router.get("", response_model=list[EventoOut])
def listar_eventos(
    db: Session = Depends(get_db),
    persona_id: int | None = None,
    limit: int = 50,
):
    query = db.query(EventoVerificacion).order_by(EventoVerificacion.creado_en.desc())
    if persona_id is not None:
        query = query.filter(EventoVerificacion.persona_id == persona_id)
    return query.limit(limit).all()
