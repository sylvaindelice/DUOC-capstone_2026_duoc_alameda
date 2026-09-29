"""Configuración de la app móvil.

Cambia BACKEND_URL según dónde esté corriendo el backend:
    - "http://127.0.0.1:8000"  -> backend en el mismo computador (modo escritorio, para la demo).
    - "http://10.0.2.2:8000"   -> backend en el computador anfitrión, visto desde el emulador de Android.
    - "http://<ip-de-tu-pc>:8000" -> backend en tu computador, visto desde un celular real en la misma red Wi-Fi.
"""
BACKEND_URL = "http://127.0.0.1:8000"
