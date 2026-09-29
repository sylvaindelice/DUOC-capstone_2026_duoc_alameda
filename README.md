AVISO

Nombre del proyecto: AVISO — Verificación de identidad mediante biometría facial

Descripción: Sistema de control de acceso que verifica la identidad de una persona comparando, en el momento, una fotografía capturada en vivo (selfie) con una fotografía de referencia registrada previamente. Si ambas imágenes corresponden a la misma persona, se otorga el acceso; en caso contrario, se deniega. El objetivo es reemplazar métodos tradicionales de control de acceso (tarjetas, revisión visual de un guardia) por una verificación automática y trazable.

Tecnologías utilizadas (lenguajes, frameworks, base de datos, cloud):

Lenguaje: Python 3.12
Backend: FastAPI, SQLAlchemy, APScheduler
Reconocimiento facial: face_recognition / dlib (motor principal), OpenCV (respaldo y procesamiento de imágenes)
Aplicación móvil: Kivy, KivyMD (Material Design)
Base de datos: SQLite
Cloud: no se utiliza infraestructura cloud; el sistema corre de forma local/on-premise (backend y app móvil en la misma red)

Instrucciones para ejecutar el proyecto localmente:

Backend:

bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

La API queda disponible en http://127.0.0.1:8000 (documentación interactiva en /docs).

Aplicación móvil:

bash
cd mobile
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
python main.py

El backend debe estar corriendo antes de iniciar la aplicación móvil, ya que esta se conecta a http://127.0.0.1:8000.

Integrantes del equipo con sus roles:

Sylvain Delice — Desarrollador full stack (backend, aplicación móvil e integración). Proyecto individual.

Metodología de trabajo del equipo (Scrum, Kanban, DevOps, etc.): Desarrollo incremental, organizado en las tres fases de la asignatura de Portafolio de Título (Fase 1: definición y planificación; Fase 2: desarrollo del backend y luego de la aplicación móvil, integrando y probando cada módulo; Fase 3: pruebas finales, ajustes y documentación). El avance se gestiona mediante un tablero personal tipo Kanban (por hacer / en progreso / hecho), dado que el proyecto es desarrollado por un solo integrante.

Arquitectura de la solución (descripción o diagrama):

[App móvil - Kivy/KivyMD]
        |
        |  HTTP (REST)
        v
[Backend - FastAPI]
        |
        |--- [Motor de reconocimiento facial: face_recognition / OpenCV]
        |
        v
[Base de datos - SQLite]

La aplicación móvil captura las fotografías (registro y verificación) desde la cámara del dispositivo y las envía al backend mediante peticiones REST. El backend gestiona el registro de personas, ejecuta la comparación biométrica facial, registra los eventos de entrada/salida en la base de datos SQLite, y expone el historial de eventos. Un proceso programado (APScheduler) se encarga de las notificaciones automáticas por correo.

