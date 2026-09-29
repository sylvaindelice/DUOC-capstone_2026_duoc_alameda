"""Pruebas del servicio de reconocimiento facial (app/face_service.py).

Corren contra el backend que esté activo en el entorno (face_recognition
si está instalado; si no, el respaldo OpenCV+LBP). No dependen de FastAPI
ni de la base de datos.
"""
import pytest

from app import face_service


def test_backend_activo_es_valido():
    assert face_service.get_backend_name() in ("face_recognition", "opencv_lbp")


def test_detecta_rostro_en_foto_de_referencia(foto_referencia_bytes):
    embedding = face_service.extract_embedding(foto_referencia_bytes)
    assert embedding is not None
    assert len(embedding) > 0


def test_imagen_sin_rostro_lanza_error(foto_sin_rostro_bytes):
    with pytest.raises(face_service.NoFaceDetectedError):
        face_service.extract_embedding(foto_sin_rostro_bytes)


def test_misma_persona_coincide(foto_referencia_bytes, foto_misma_persona_bytes):
    """La foto de referencia comparada contra una segunda captura de la misma
    persona (reescalada/recomprimida) debe considerarse una coincidencia."""
    resultado = face_service.verify(foto_referencia_bytes, foto_misma_persona_bytes)
    assert resultado.is_match is True
    assert resultado.backend == face_service.get_backend_name()


def test_persona_distinta_no_coincide(foto_referencia_bytes, foto_otra_imagen_bytes):
    """Compara la referencia contra una imagen claramente distinta. Se usa como
    sustituto de 'otra persona' porque no hay un segundo rostro real bundled
    en el entorno de pruebas; lo relevante es verificar que el umbral rechaza
    comparaciones que no coinciden."""
    try:
        resultado = face_service.verify(foto_referencia_bytes, foto_otra_imagen_bytes)
    except face_service.NoFaceDetectedError:
        pytest.skip("La imagen sustituta no produjo una detección de rostro en este backend.")
    assert resultado.is_match is False


def test_umbral_personalizado_afecta_la_decision(foto_referencia_bytes, foto_misma_persona_bytes):
    """Un umbral absurdamente estricto debe hacer fallar incluso una coincidencia real."""
    ref = face_service.extract_embedding(foto_referencia_bytes)
    probe = face_service.extract_embedding(foto_misma_persona_bytes)

    if face_service.get_backend_name() == "face_recognition":
        umbral_imposible = 0.0  # ninguna distancia real es exactamente 0
    else:
        umbral_imposible = 1.01  # ninguna correlación real supera 1.0

    resultado = face_service.compare_embeddings(ref, probe, threshold=umbral_imposible)
    assert resultado.is_match is False
