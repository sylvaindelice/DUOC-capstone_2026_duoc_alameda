"""Servicio de reconocimiento facial.

Backend principal: `face_recognition` (basado en dlib). Genera un embedding
de 128 dimensiones por rostro y compara dos embeddings por distancia
euclidiana. Es el motor documentado en la propuesta de proyecto
(sección 5.2 — Visión computacional).

Backend de respaldo (fallback) automático: si `face_recognition` no está
instalado en el equipo (por ejemplo, porque dlib no pudo compilarse), el
servicio usa un método clásico basado únicamente en OpenCV y scikit-image:
detección de rostro con Haar Cascade + histograma de patrones binarios
locales (LBP) para comparar. Es menos preciso que un embedding profundo,
pero no depende de librerías pesadas de compilar, así que el sistema
puede seguir instalándose y ejecutándose igual.

El backend activo se decide una sola vez al importar este módulo y queda
disponible en `get_backend_name()`. El embedding de cada persona se guarda
junto con el nombre del backend usado (ver app/models.py) para no comparar
embeddings generados por motores distintos.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from skimage.feature import local_binary_pattern

try:
    import face_recognition  # type: ignore

    _BACKEND = "face_recognition"
except ImportError:  # pragma: no cover - depende del entorno de instalación
    face_recognition = None
    _BACKEND = "opencv_lbp"


# Distancia euclidiana entre embeddings de face_recognition: menor = más parecido.
DEFAULT_THRESHOLD_FACE_RECOGNITION = 0.6
# Correlación entre histogramas LBP: mayor = más parecido.
DEFAULT_THRESHOLD_OPENCV_LBP = 0.90

_FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


class NoFaceDetectedError(Exception):
    """No se detectó ningún rostro en la imagen entregada."""


@dataclass
class MatchResult:
    is_match: bool
    score: float
    backend: str
    detail: str = ""


def get_backend_name() -> str:
    return _BACKEND


def _load_image(source: Union[str, Path, bytes]) -> np.ndarray:
    """Carga una imagen desde una ruta de archivo o desde bytes en memoria (BGR, como OpenCV)."""
    if isinstance(source, (str, Path)):
        img = cv2.imread(str(source))
        if img is None:
            raise ValueError(f"No se pudo leer la imagen: {source}")
        return img
    arr = np.frombuffer(source, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("No se pudo decodificar la imagen recibida.")
    return img


def _detect_largest_face(img_bgr: np.ndarray) -> np.ndarray:
    """Detecta rostros con Haar Cascade y devuelve el recorte en escala de grises del más grande."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        raise NoFaceDetectedError("No se detectó un rostro en la imagen.")
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])  # el más grande = más cercano a la cámara
    return gray[y : y + h, x : x + w]


def _lbp_histogram(face_gray: np.ndarray, size: tuple[int, int] = (128, 128)) -> np.ndarray:
    """Calcula un histograma LBP uniforme normalizado para el recorte de rostro."""
    face = cv2.resize(face_gray, size)
    lbp = local_binary_pattern(face, P=8, R=1, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 11), range=(0, 10), density=True)
    return hist.astype("float32")


def _embed_face_recognition(img_bgr: np.ndarray) -> np.ndarray:
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    if not locations:
        raise NoFaceDetectedError("No se detectó un rostro en la imagen.")
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    return np.asarray(encodings[0], dtype="float32")


def extract_embedding(image: Union[str, Path, bytes]) -> np.ndarray:
    """Extrae la representación facial (embedding o histograma LBP) del rostro principal de una imagen."""
    img = _load_image(image)
    if _BACKEND == "face_recognition":
        return _embed_face_recognition(img)
    face = _detect_largest_face(img)
    return _lbp_histogram(face)


def compare_embeddings(
    embedding_a: np.ndarray, embedding_b: np.ndarray, threshold: float | None = None
) -> MatchResult:
    """Compara dos representaciones faciales ya extraídas y decide si corresponden a la misma persona."""
    if _BACKEND == "face_recognition":
        th = threshold if threshold is not None else DEFAULT_THRESHOLD_FACE_RECOGNITION
        distance = float(np.linalg.norm(embedding_a - embedding_b))
        return MatchResult(
            is_match=distance <= th,
            score=distance,
            backend=_BACKEND,
            detail="distancia euclidiana entre embeddings (menor = más parecido)",
        )

    th = threshold if threshold is not None else DEFAULT_THRESHOLD_OPENCV_LBP
    correlation = float(cv2.compareHist(embedding_a, embedding_b, cv2.HISTCMP_CORREL))
    return MatchResult(
        is_match=correlation >= th,
        score=correlation,
        backend=_BACKEND,
        detail="correlación entre histogramas LBP (mayor = más parecido)",
    )


def verify(
    reference_image: Union[str, Path, bytes],
    probe_image: Union[str, Path, bytes],
    threshold: float | None = None,
) -> MatchResult:
    """Compara la imagen de referencia (documento) contra la imagen capturada en vivo (selfie)."""
    ref_embedding = extract_embedding(reference_image)
    probe_embedding = extract_embedding(probe_image)
    return compare_embeddings(ref_embedding, probe_embedding, threshold=threshold)
