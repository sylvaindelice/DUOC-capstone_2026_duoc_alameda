"""App móvil (Kivy/KivyMD) — Sistema de verificación de identidad.

Pantallas:
    - Registro:      captura la foto de referencia y registra a la persona.
    - Personas:       lista a las personas registradas (elegir con quién verificar).
    - Verificación:   captura una selfie y la envía al backend para comparar.
    - Historial:      muestra los últimos eventos de esa persona.

Para ejecutar en modo escritorio (útil para la demo ante el profesor, sin
necesitar compilar un APK):

    pip install -r requirements.txt
    python main.py

La URL del backend se configura en config.py (por defecto http://127.0.0.1:8000,
es decir, el backend corriendo en el mismo computador).
"""
from __future__ import annotations

import os
import tempfile

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem, MDListItemHeadlineText

from api_client import ApiClient, ApiError
from config import BACKEND_URL



class RegistroScreen(Screen):
    pass


class PersonasScreen(Screen):
    pass


class VerificacionScreen(Screen):
    resultado_texto = StringProperty("")
    resultado_color = ListProperty([0.5, 0.5, 0.5, 1])
    persona_id = None
    persona_nombre = StringProperty("")


class HistorialScreen(Screen):
    pass



class IdentidadApp(MDApp):
    persona_seleccionada = None

    def build(self):
        self.title = "Verificación de Identidad"
        self.theme_cls.primary_palette = "Indigo"
        self.api = ApiClient(BACKEND_URL)
        return None  # el root se define en identidad.kv (ScreenManager)

    def on_start(self):
        self.refrescar_personas()

    # ---------------- Registro ----------------
    def capturar_y_registrar(self):
        screen = self.root.get_screen("registro")
        nombre = screen.ids.campo_nombre.text.strip()
        email = screen.ids.campo_email.text.strip()
        camera = screen.ids.camera_registro

        if not nombre or not email:
            self._mostrar_snackbar("Completa nombre y correo antes de capturar la foto.")
            return

        foto_path = self._exportar_frame(camera, "referencia")
        if foto_path is None:
            return

        try:
            persona = self.api.registrar_persona(nombre, email, foto_path)
        except ApiError as exc:
            self._mostrar_snackbar(f"No se pudo registrar: {exc}")
            return
        except Exception as exc:  # errores de red, backend apagado, etc.
            self._mostrar_snackbar(f"Error de conexión con el backend: {exc}")
            return

        self._mostrar_snackbar(f"Persona registrada: {persona['nombre']} (ID {persona['id']})")
        screen.ids.campo_nombre.text = ""
        screen.ids.campo_email.text = ""
        self.refrescar_personas()
        self.root.current = "personas"

    # ---------------- Selección de persona ----------------
    def refrescar_personas(self):
        try:
            personas = self.api.listar_personas()
        except Exception:
            personas = []
        pantalla = self.root.get_screen("personas")
        lista = pantalla.ids.lista_personas
        lista.clear_widgets()
        for p in personas:
            item = MDListItem(
                MDListItemHeadlineText(text=f"{p['nombre']} — {p['email']}"),
            )
            item.bind(on_release=lambda _inst, p=p: self.seleccionar_persona(p))
            lista.add_widget(item)
    def seleccionar_persona(self, persona: dict):
        self.persona_seleccionada = persona
        pantalla = self.root.get_screen("verificacion")
        pantalla.persona_id = persona["id"]
        pantalla.persona_nombre = persona["nombre"]
        pantalla.resultado_texto = ""
        self.root.current = "verificacion"

    # ---------------- Verificación ----------------
    def capturar_y_verificar(self):
        pantalla = self.root.get_screen("verificacion")
        if pantalla.persona_id is None:
            self._mostrar_snackbar("Primero selecciona una persona.")
            return

        camera = pantalla.ids.camera_verificacion
        selfie_path = self._exportar_frame(camera, "selfie")
        if selfie_path is None:
            return

        try:
            resultado = self.api.verificar(pantalla.persona_id, selfie_path)
        except ApiError as exc:
            pantalla.resultado_texto = f"Error: {exc}"
            pantalla.resultado_color = [0.8, 0.2, 0.2, 1]
            return
        except Exception as exc:
            pantalla.resultado_texto = f"Error de conexión con el backend: {exc}"
            pantalla.resultado_color = [0.8, 0.2, 0.2, 1]
            return

        concedido = resultado["resultado"] == "concedido"
        pantalla.resultado_color = [0.2, 0.7, 0.3, 1] if concedido else [0.8, 0.2, 0.2, 1]
        pantalla.resultado_texto = (
            f"{resultado['mensaje']}\n"
            f"Tipo de evento: {resultado['tipo_evento']}\n"
            f"Puntaje: {resultado['score']:.3f}"
        )

    # ---------------- Historial ----------------
    def refrescar_historial(self):
        pantalla_ver = self.root.get_screen("verificacion")
        pantalla_hist = self.root.get_screen("historial")
        lista = pantalla_hist.ids.lista_eventos
        lista.clear_widgets()

        if pantalla_ver.persona_id is None:
            return
        try:
            eventos = self.api.listar_eventos(persona_id=pantalla_ver.persona_id)
        except Exception:
            eventos = []
        for e in eventos:
            texto = f"{e['creado_en']} — {e['tipo']} ({e['resultado']}) score={e['score']:.3f}"
            lista.add_widget(MDListItem(MDListItemHeadlineText(text=texto)))

    # ---------------- Utilidades ----------------
    def _exportar_frame(self, camera, prefijo: str) -> str | None:
        """Exporta el cuadro actual de un widget Camera de Kivy a un PNG temporal."""
        if camera.texture is None:
            self._mostrar_snackbar("La cámara todavía no está lista, espera un segundo e intenta de nuevo.")
            return None
        path = os.path.join(tempfile.gettempdir(), f"{prefijo}_{int(Clock.get_boottime() * 1000)}.png")
        camera.export_to_png(path)
        return path

    def _mostrar_snackbar(self, mensaje: str):
        try:
            from kivymd.uix.snackbar import MDSnackbar
            from kivymd.uix.label import MDLabel

            MDSnackbar(MDLabel(text=mensaje)).open()
        except Exception:
            print(mensaje)  # respaldo si la versión de KivyMD no trae MDSnackbar


if __name__ == "__main__":
    IdentidadApp().run()
