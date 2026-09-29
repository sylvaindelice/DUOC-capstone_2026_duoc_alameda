"""Fixtures compartidos para las pruebas.

Genera imágenes de prueba a partir de `skimage.data`, que trae fotografías
reales bundled con la librería (no se necesita internet ni archivos
externos para correr las pruebas).
"""
import io

import cv2
import numpy as np
import pytest
from skimage import data


def _encode_png(img_rgb: np.ndarray) -> bytes:
    bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".png", bgr)
    assert ok
    return buf.tobytes()


@pytest.fixture(scope="session")
def foto_referencia_bytes() -> bytes:
    """Foto con un rostro real detectable (astronauta, de skimage.data)."""
    return _encode_png(data.astronaut())


@pytest.fixture(scope="session")
def foto_misma_persona_bytes() -> bytes:
    """La misma foto de referencia, pero re-comprimida y con un leve reescalado,
    simulando una segunda captura de la misma persona en otro momento."""
    img = data.astronaut()
    h, w = img.shape[:2]
    resized = cv2.resize(img, (int(w * 0.97), int(h * 0.97)))
    resized = cv2.resize(resized, (w, h))
    return _encode_png(resized)


@pytest.fixture(scope="session")
def foto_otra_imagen_bytes() -> bytes:
    """Una imagen distinta, usada como sustituto de 'persona distinta' para
    probar que el sistema rechaza correctamente una comparación que no coincide.
    (No se dispone de un segundo rostro real bundled; ver docstring del test)."""
    return _encode_png(data.coins() if data.coins().ndim == 3 else cv2_gray_to_rgb(data.coins()))


def cv2_gray_to_rgb(img_gray: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)


@pytest.fixture(scope="session")
def foto_sin_rostro_bytes() -> bytes:
    """Una imagen sin ningún rostro (para probar NoFaceDetectedError)."""
    return _encode_png(data.camera() if data.camera().ndim == 3 else cv2_gray_to_rgb(data.camera()))
