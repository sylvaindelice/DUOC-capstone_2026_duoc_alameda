"""Cliente HTTP para que la app móvil (Kivy/KivyMD) consuma el backend FastAPI."""
from __future__ import annotations

import requests


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _handle(self, resp: requests.Response) -> dict:
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise ApiError(str(detail), resp.status_code)
        return resp.json()

    def registrar_persona(self, nombre: str, email: str, foto_path: str) -> dict:
        with open(foto_path, "rb") as f:
            files = {"foto": ("foto.png", f, "image/png")}
            data = {"nombre": nombre, "email": email}
            resp = requests.post(f"{self.base_url}/personas", data=data, files=files, timeout=20)
        return self._handle(resp)

    def listar_personas(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/personas", timeout=15)
        return self._handle(resp)

    def verificar(self, persona_id: int, selfie_path: str) -> dict:
        with open(selfie_path, "rb") as f:
            files = {"selfie": ("selfie.png", f, "image/png")}
            data = {"persona_id": str(persona_id)}
            resp = requests.post(f"{self.base_url}/verificar", data=data, files=files, timeout=20)
        return self._handle(resp)

    def listar_eventos(self, persona_id: int | None = None, limit: int = 20) -> list[dict]:
        params = {"limit": limit}
        if persona_id is not None:
            params["persona_id"] = persona_id
        resp = requests.get(f"{self.base_url}/eventos", params=params, timeout=15)
        return self._handle(resp)
