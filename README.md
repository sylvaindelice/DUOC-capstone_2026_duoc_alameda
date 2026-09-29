# Sistema móvil de verificación de identidad mediante comparación biométrica facial

Código base del proyecto de título. Sigue la arquitectura de la propuesta:
un cliente móvil (Kivy/KivyMD) captura fotos y las envía a un backend
(FastAPI) que hace todo el procesamiento biométrico, guarda el resultado
en base de datos y envía notificaciones por correo.

```
identidad-app/
├── backend/     API (FastAPI) + reconocimiento facial + base de datos + scheduler + correo
├── mobile/      App móvil (Kivy/KivyMD) que consume la API
└── .vscode/     Configuración lista para abrir y depurar el proyecto en VS Code
```

## 0. Abrir en Visual Studio Code

1. Descomprime el proyecto y ábrelo con "Archivo → Abrir carpeta..." seleccionando la carpeta `identidad-app` completa.
2. Instala la extensión **Python** (te la sugiere VS Code al abrir un `.py`).
3. Crea los entornos virtuales como se indica en las secciones 1 y 2 más abajo (`backend/venv` y `mobile/venv`) — el proyecto ya viene configurado (`.vscode/launch.json`) para usar esas rutas exactas.
4. Con eso, en la pestaña "Run and Debug" (`Ctrl+Shift+D`) vas a ver tres configuraciones listas para correr con F5:
   - **Backend: FastAPI (uvicorn --reload)** — levanta la API con recarga automática.
   - **Backend: pytest (todas las pruebas)** — corre la suite de pruebas con el depurador conectado (puedes poner breakpoints).
   - **Mobile: app Kivy/KivyMD (escritorio)** — abre la app móvil en modo escritorio para hacer pruebas/demo.

Si usaste otro nombre para el entorno virtual, o lo pusiste en otra ruta, ajusta la clave `"python"` de cada configuración en `.vscode/launch.json`.

## 1. Backend

### Instalación

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Esto instala el motor de reconocimiento facial de respaldo (OpenCV + LBP),
que no requiere compilar nada. **Para usar el motor principal documentado
en la propuesta** (`face_recognition`, basado en dlib, más preciso),
instala además:

```bash
pip install -r requirements-face_recognition.txt
```

Si esa instalación falla en tu equipo (dlib necesita cmake y un compilador
de C++), no pasa nada: `app/face_service.py` detecta automáticamente qué
motor está disponible y usa el que corresponda. No hay que tocar ningún
otro archivo — todo el resto del sistema es igual con cualquiera de los
dos motores.

### Configuración

```bash
cp .env.example .env
```

Por defecto `APP_SMTP_ENABLED=False`, así que los correos no se envían de
verdad: solo quedan en el log del servidor. Es útil para probar todo el
flujo sin configurar una cuenta SMTP. Cuando quieras que se envíen
correos reales, pon `APP_SMTP_ENABLED=True` y completa los datos SMTP
(por ejemplo, una cuenta de Gmail con una "contraseña de aplicación").

### Ejecutar

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`. Documentación
interactiva automática (generada por FastAPI) en
`http://127.0.0.1:8000/docs` — sirve para probar los endpoints a mano,
sin la app móvil, subiendo imágenes desde el navegador.

Al arrancar, el backend crea la base de datos SQLite (`identidad.db`) si
no existe, y arranca el scheduler que revisa la asistencia de cada
persona cada `APP_SCHEDULER_INTERVAL_MINUTOS` (60 por defecto).

### Endpoints principales

| Método | Ruta          | Descripción                                                       |
|--------|---------------|--------------------------------------------------------------------|
| POST   | `/personas`   | Registra una persona con su foto de referencia (nombre, email, foto) |
| GET    | `/personas`   | Lista las personas registradas                                     |
| POST   | `/verificar`  | Compara una selfie contra la referencia de una persona; concede o deniega el acceso, y registra entrada/salida |
| GET    | `/eventos`    | Historial de verificaciones (filtrable por `persona_id`)           |
| GET    | `/salud`      | Chequeo simple, indica qué motor facial está activo                |

### Pruebas

```bash
pytest
```

`tests/test_attendance.py`, `tests/test_face_service.py` y
`tests/test_email_service.py` no dependen de FastAPI ni de la base de
datos, así que corren en cualquier entorno con las dependencias base
instaladas. `tests/test_api.py` prueba los endpoints HTTP de punta a
punta (registro → verificación → historial); si FastAPI o SQLAlchemy no
están instalados, esas pruebas se omiten automáticamente (`SKIPPED`) en
vez de fallar.

> **Nota sobre este entorno de desarrollo:** el código de este proyecto
> se generó en un entorno sin acceso a internet para instalar paquetes
> (no podía llegar a PyPI), así que `fastapi`, `sqlalchemy` y
> `apscheduler` no se pudieron instalar ni probar ahí. Por eso
> `tests/test_api.py` aparece como `SKIPPED` si lo corres tal cual se
> entregó. Sí se pudo instalar y probar todo lo demás: la lógica de
> reconocimiento facial (con el motor de respaldo OpenCV+LBP, porque
> `face_recognition`/dlib tampoco se pudo instalar ahí), el cálculo de
> la ventana móvil de 24 horas, y el servicio de correo. En tu
> computador, con internet normal, `pip install -r requirements.txt`
> instala todo sin problema y las 4 pruebas de `test_api.py` deberían
> pasar igual que el resto.

## 2. App móvil

### Instalación

```bash
cd mobile
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuración

Edita `mobile/config.py` y ajusta `BACKEND_URL` según dónde esté
corriendo el backend (ver los comentarios en el archivo — cambia según
si pruebas en tu propio computador, en un emulador de Android, o en un
celular real conectado a la misma red Wi-Fi).

### Ejecutar (modo escritorio, para la demo)

Con el backend ya corriendo en otra terminal:

```bash
python main.py
```

Esto abre la app con la cámara del computador — perfecto para hacer la
demo ante el profesor sin necesitar compilar un APK.

### Compilar el APK (Android)

```bash
pip install buildozer
buildozer android debug
```

Esto genera un `.apk` en `mobile/bin/`. Requiere tener instalado el SDK
de Android (buildozer lo descarga la primera vez, puede tardar bastante).

### Pantallas

1. **Registro** — captura la foto de referencia (ej. la foto del carnet) y registra a la persona con nombre y correo.
2. **Personas** — lista a las personas registradas; se elige con quién verificar.
3. **Verificación** — captura una selfie en vivo y la envía al backend; muestra si el acceso fue concedido o denegado, y si se registró como entrada o salida.
4. **Historial** — muestra los últimos eventos de verificación de esa persona.

## 3. Cómo se conecta esto con la propuesta de proyecto

- La comparación biométrica implementa la sección 5.1 (flujo general) y
  5.2 (componentes) de la propuesta: cliente móvil liviano + todo el
  procesamiento en el backend.
- El control de asistencia implementa la sección 5.3: ventana móvil de
  24 horas por persona (no un horario fijo de oficina), con aviso previo
  a las 20h y aviso final a las 24h desde la última entrada — ver
  `app/attendance.py` y `tests/test_attendance.py` (incluye un test que
  reproduce exactamente el caso que preguntó el profesor: una persona
  con turno 09:00–20:00 recibe los mismos avisos que una de 08:00–18:00).
- El acceso está disponible 24/7: la verificación de identidad no
  depende de ningún horario.

## 4. Próximos pasos sugeridos

- Afinar el umbral de decisión (`APP_FACE_MATCH_THRESHOLD`) con fotos
  reales de prueba, y medir exactitud / FAR / FRR como se documentó en
  la propuesta (sección 8).
- Si se instala `face_recognition`, volver a registrar a las personas
  (el embedding de un motor no es compatible con el del otro — por eso
  se guarda `embedding_backend` junto a cada persona).
- Agregar la prueba de vida (liveness) mencionada como objetivo opcional.
