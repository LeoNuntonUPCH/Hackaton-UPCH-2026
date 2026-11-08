# SATQ Digital — prototipo de demostración

Sistema de Alerta Temprana de Quebradas del Perú.
Hackathon Interdisciplinaria FACI 2026 · UPCH · Reto 4 (Clima, agua y gestión de riesgos).

> **Todos los datos de este sistema son simulados.** No proviene información de
> SENAMHI ni de INAIGEM, no hay sensores conectados y no se envía ningún mensaje.
> No debe usarse para decisiones de emergencia.

---

## Cómo arrancarlo

### En Windows

Doble clic en **`iniciar.bat`**. Luego abre <http://127.0.0.1:8000> en el navegador.

El script detecta si FastAPI está instalado y, si no lo está, arranca el servidor
de respaldo automáticamente.

### Desde la terminal

```bash
# Versión completa: FastAPI + API documentada
pip install -r requirements.txt
python -m uvicorn app:app --port 8000

# Versión de respaldo: solo librería estándar + Jinja2
python servidor_demo.py
```

Ambas sirven exactamente las mismas pantallas. La diferencia es que `app.py`
añade la API JSON documentada en <http://127.0.0.1:8000/docs>.

---

## Qué hay dentro

```
satq-digital/
├── app.py                      Aplicación FastAPI: pantallas + API JSON
├── servidor_demo.py            Servidor de respaldo, sin dependencias externas
├── iniciar.bat
├── diagnostico.py              Diagnóstico de arranque
├── pruebas_flujo.py            Pruebas de los flujos interactivos
├── pruebas_ingesta.py          Pruebas de POST /api/ingesta (unittest)
├── pruebas_alertas.py          Pruebas de POST /api/alertas (unittest)
├── requirements.txt
├── requirements-postgres.txt   Solo si usas PostgreSQL (psycopg)
├── requirements-dev.txt        Solo para desarrollo (pytest, ruff, mypy)
├── pyproject.toml              Configuración de pytest, ruff y mypy
├── tests/                      Pruebas con pytest
├── n8n/                        Workflow de ingesta demo + guía
├── mensajeria/                 Canales SMS (Twilio/Vonage/Infobip) y simulado
├── satqito/                    Bot de Telegram (suscripción y consulta)
├── docs/                       Observabilidad, mensajería y suscripción
├── .github/workflows/ci.yml    Integración continua
└── satq/
    ├── motor.py                Motor de clasificación de riesgo  ← el corazón
    ├── datos.py                Escenario simulado (24 quebradas, 7 alertas)
    ├── estado.py               Fachada del estado; delega en un repositorio
    ├── repositorio.py          Interfaz de almacenamiento
    ├── repositorio_memoria.py  Backend por defecto (se reinicia)
    ├── almacen_postgres.py     Backend opcional PostgreSQL
    ├── migraciones/            Esquema SQL (001_inicial.sql)
    ├── observabilidad.py       Logs, métricas y estado de salud
    ├── graficos.py             Gráfico y mapa en SVG, generados en el servidor
    ├── vistas.py               Qué datos ve cada pantalla
    ├── plantillas.py           Entorno Jinja2
    ├── templates/              10 plantillas HTML
    └── static/css/             Una hoja de estilos
```

No hay dependencias de CDN ni de internet: los gráficos y el mapa se generan
como SVG en el servidor. El prototipo funciona sin conexión.

---

## Las 8 pantallas

| Ruta | Pantalla |
|---|---|
| `/login` | Acceso (estático, no autentica) |
| `/dashboard` | Monitoreo territorial |
| `/mapa` | Mapa de riesgo |
| `/quebrada/huaycoloro` | Detalle de quebrada |
| `/alertas` | Centro de alertas |
| `/notificaciones` | Gestión de notificaciones |
| `/notificaciones/confirmar` | Confirmación de envío |
| `/configuracion` | Configuración y fuentes de datos |

Dos pantallas adicionales que no estaban en el diseño: `/quebradas`
(listado completo) y `/reportes` (agregados del escenario).

`/suscripcion` permite registrar un teléfono de prueba y una zona: el sistema
asigna la quebrada más cercana y envía avisos a sus suscriptores.

---

## Acceso y seguridad

El login es **de demostración**: no autentica, no gestiona sesiones y no protege
datos. Solo elige el perfil (`Autoridad` o `Personal técnico`) para recorrer la
interfaz, y la pantalla lo advierte de forma visible. No escribas credenciales
reales.

La única protección real está en la **API de ingesta**: `POST /api/ingesta` y
`POST /api/alertas` exigen el header `X-API-Key` y la variable de entorno
`SATQ_INGESTA_API_KEY`. Si la variable no está configurada, responden `503`; si
la clave no coincide, `401`.

No hay envío real de mensajes ni integraciones oficiales conectadas.

---

## El motor de umbrales

Es la regla única del sistema y vive en `satq/motor.py`:

```
acumulado < 20 mm/6 h   →  Bajo
20 ≤ acumulado < 30     →  Moderado
30 ≤ acumulado < 40     →  Alto
acumulado ≥ 40          →  Crítico
sin lectura             →  Sin datos   (no se asume "bajo")
```

Los cuatro límites y la ventana de acumulación son editables desde
`/configuracion`. Al guardarlos, el sistema **recalcula el nivel de todas las
alertas abiertas** y deja constancia en el historial de parámetros.

Se puede comprobar la regla sin pasar por la interfaz:

```
GET /api/evaluar?acumulado_mm=42
```

---

## Qué está implementado y qué no

La propuesta describe una arquitectura completa. Este prototipo implementa una
parte y es explícito sobre el resto, tanto en la documentación como dentro de la
propia interfaz (`/configuracion` → pestaña *Fuentes y conexiones*).

| Componente | Propuesta | En este prototipo |
|---|---|---|
| Backend | Python · FastAPI | **Implementado** |
| Motor de umbrales | Reglas configurables | **Implementado** |
| Panel web | Streamlit o React | HTML/CSS + Jinja2 servido por FastAPI |
| Base de datos | PostgreSQL | Opcional: PostgreSQL o memoria (por defecto) |
| Automatización | n8n | Demo: workflow de ingesta en `n8n/` |
| Bot de Telegram | — | **Implementado:** Satqito (registro y consulta) |
| Mensajería | API WhatsApp / SMS | SMS real opcional (Infobip/Twilio/Vonage); simulado por defecto |
| Fuentes de datos | SENAMHI · INAIGEM | No conectadas; series sintéticas |

La diferencia entre "implementado", "demo" y "simulado" importa: la persistencia
en PostgreSQL funciona, pero es opcional; el workflow de n8n existe, pero no se
conecta a fuentes oficiales; y la mensajería puede enviar SMS reales solo a
números autorizados, con modo simulado por defecto.

---

## Persistencia (opcional)

Por defecto el prototipo usa **memoria**: al reiniciar el servidor vuelve al
escenario inicial. Eso es justo lo que se quiere para una demostración repetible.

Si defines `SATQ_DB=postgres`, el estado se guarda en PostgreSQL y **sobrevive a
los reinicios**. La primera vez la base se siembra sola y `POST /api/reiniciar`
la devuelve al escenario inicial.

1. Crea una base `satq` en PostgreSQL.
2. Aplica el esquema (o deja que la app lo cree al arrancar):
   `satq/migraciones/001_inicial.sql`
3. Instala el driver opcional:
   ```powershell
   pip install -r requirements-postgres.txt
   ```
4. Arranca con:
   ```powershell
   $env:SATQ_DB="postgres"
   $env:SATQ_DSN="postgresql://postgres:TUCLAVE@localhost:5432/satq"
   python -m uvicorn app:app --port 8000
   ```

`SATQ_DSN` contiene la contraseña: **no lo guardes en el repositorio**. Si no
defines `SATQ_DB`, todo funciona en memoria y sin PostgreSQL. El servidor de
respaldo siempre usa memoria.

---

## Mensajería SMS

El canal principal es **SMS**, porque el destinatario no necesita datos móviles
ni WiFi: solo cobertura celular. El envío real se activa por variables de
entorno; sin ellas, el sistema funciona en modo **simulado** para desarrollo,
pruebas y CI.

```powershell
# Twilio
$env:SATQ_SMS_MODO="real"
$env:SATQ_SMS_PROVEEDOR="twilio"
$env:SATQ_TWILIO_SID="AC..."
$env:SATQ_TWILIO_TOKEN="..."
$env:SATQ_TWILIO_FROM="+1..."
$env:SATQ_SMS_DESTINO="+51..."
$env:SATQ_SMS_MAX_ENVIOS="10"
```

También se admite **Vonage** (`SATQ_SMS_PROVEEDOR=vonage`) e **Infobip**
(`SATQ_SMS_PROVEEDOR=infobip`, con `SATQ_INFOBIP_API_KEY`,
`SATQ_INFOBIP_BASE_URL` y `SATQ_INFOBIP_FROM`). Cada envío registra estado,
proveedor, id externo, error, intentos y destino enmascarado. Hay un tope de
envíos, un único destino configurado e idempotencia por alerta + canal +
plantilla.

Detalle completo en `docs/mensajeria.md`.

---

## Suscripción comunitaria

`/suscripcion` permite que un vecino registre su teléfono de prueba y su zona.
Si comparte su ubicación, el sistema calcula la **quebrada más cercana**; si no,
usa la zona seleccionada. El registro exige consentimiento explícito y el
teléfono se muestra enmascarado.

Los suscriptores activos de una quebrada reciben los avisos cuando se despacha
una alerta:

- **Manual:** botón "Enviar a suscriptores" en `/suscripcion`.
- **Automático:** con `SATQ_ALERTAS_AUTO=1`, al crearse una alerta nueva.

En modo real, el envío solo se permite a números incluidos en
`SATQ_SMS_DESTINOS_PERMITIDOS`. Hay tope de envíos e idempotencia por alerta,
canal, plantilla y teléfono. La baja se hace desde la misma pantalla.

Detalle completo en `docs/suscripcion.md`.

---

## Satqito (bot de Telegram)

`satqito/` es un bot independiente que habla con la API de SATQ. **No modifica
alertas**: solo consulta el estado, registra suscripciones y verifica el teléfono
con un código SMS de 4 dígitos. Las alertas se siguen enviando por **SMS**.

### Lanzador para la demo

Haz doble clic en **`iniciar_demo.bat`** (archivo local, no se sube al repo).
Levanta SATQ y Satqito, y se detiene al cerrar las ventanas.

Comparte el bot: <https://t.me/SatqitoAlertasBot>.

### Comportamiento para el jurado

- Cada persona que se registra recibe su **propio SMS** de verificación en el
  número que escribió.
- `/probar` envía un SMS de prueba **solo a esa persona**, no a todos.
- Las alertas reales se envían a los suscriptores de la quebrada afectada.
- Con `SATQ_SMS_PERMITIR_ABIERTOS=1` se permite que cualquier número se registre,
  con un tope (`SATQ_SMS_MAX_ENVIOS`) para controlar el costo.

### Opción manual

```powershell
# Terminal 1
$env:SATQ_BOT_API_KEY="clave-interna-del-bot"
python -m uvicorn app:app --host 127.0.0.1 --port 8000

# Terminal 2
$env:SATQ_TELEGRAM_BOT_TOKEN="123456:ABC..."
$env:SATQ_BOT_API_KEY="clave-interna-del-bot"
$env:SATQ_API_URL="http://127.0.0.1:8000"
python -m satqito
```

Flujo: `/start` → saludo y estado del país → consentimiento → teléfono →
ubicación → quebrada más cercana → código SMS de 4 dígitos → suscripción
registrada. Comandos: `/estado`, `/probar`, `/baja`, `/ayuda`.

No se necesitan grupos de Telegram: el bot funciona por chat directo.

Detalle completo en `satqito/README.md`.

---

## Sobre los datos

Las series de lluvia son sintéticas y **deterministas**: se generan con una
semilla fija, de modo que el escenario es idéntico en cada ejecución. El
episodio simulado termina en la **hora actual de Perú (UTC-5)**, por eso el
acumulado móvil sube desde casi cero.

Las ubicaciones de las quebradas son reales; los niveles de riesgo asociados a
ellas, no. Las capas de zonas seguras, rutas de evacuación y exposición aparecen
deliberadamente bloqueadas y marcadas como «sin información verificada»: señalar
una zona segura que nadie ha verificado sería el error más grave que podría
cometer un sistema como este.

---

## Pruebas

```bash
# Con el servidor en marcha, en otra terminal:
python pruebas_flujo.py
```

Comprueba los ocho flujos: validar una alerta, cambiar su estado, registrar un
envío simulado, guardar umbrales, el recálculo de niveles, el rechazo de
umbrales inválidos y el alta de una quebrada.

Además, el repositorio incluye pruebas automatizadas del motor, del estado y del
repositorio, y de los endpoints de ingesta:

```bash
# Dependencias de desarrollo (no hacen falta para la demo)
pip install -r requirements-dev.txt

# Motor, estado y repositorio
python -m pytest -q

# Calidad de código
python -m ruff check .
python -m mypy

# Endpoints de ingesta y creación de alertas
python -m unittest pruebas_ingesta pruebas_alertas -v
```

En total son **103 pruebas con pytest**, **17 con unittest** y **8 flujos** de
interfaz. La carpeta `tests/` cubre los límites del motor, `sin_datos`, la
ventana móvil, las transiciones de alertas, el recálculo de umbrales, la
idempotencia de la ingesta, el contrato del repositorio y la evaluación
observacional de eventos. El método y los requisitos de datos están en
[Validación y evidencia](docs/validacion_y_evidencia.md).

### Integración continua

El workflow `.github/workflows/ci.yml` se ejecuta en cada push y Pull Request y
corre `pytest`, `ruff`, `mypy`, las pruebas `unittest` de la API y
`diagnostico.py`. No necesita servidor ni base de datos.

---

## API JSON (solo con `app.py`)

| Endpoint | Qué devuelve |
|---|---|
| `GET /api/resumen` | Conteos por nivel y por estado de gestión |
| `GET /api/quebradas` | Las 24 quebradas con acumulado y nivel |
| `GET /api/quebradas/{codigo}` | Serie de acumulado y evaluación |
| `GET /api/alertas` | Alertas del escenario |
| `GET /api/evaluar?acumulado_mm=42` | Aplica el motor a un valor cualquiera |
| `POST /api/ingesta` | Recibe lecturas desde n8n y devuelve la evaluación |
| `POST /api/alertas` | Crea una alerta si el nivel es alto o crítico |
| `POST /api/reiniciar` | Devuelve el escenario a su punto inicial |
| `GET /health` | Estado de salud del servicio y de la base de datos |
| `GET /api/metricas` | Peticiones, errores y tiempos acumulados |

Documentación interactiva en `/docs`.

### Ingesta desde n8n

El endpoint `POST /api/ingesta` requiere la variable `SATQ_INGESTA_API_KEY` y el
header `X-API-Key`. Si la variable no está configurada, responde `503`; si la
clave no coincide, `401`.

```powershell
$env:SATQ_INGESTA_API_KEY="satq-demo-local"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Ejemplo de cuerpo:

```json
{
  "quebrada": "huaycoloro",
  "fuente": "n8n-demo",
  "idempotency_key": "demo-2026-10-29-01",
  "lecturas": [
    {"mm_h": 12.5},
    {"mm_h": 14.0}
  ]
}
```

La respuesta incluye `nivel`, `acumulado_mm` y `alerta_requerida`. No crea
alertas: solo informa si el nivel es `alto` o `critico`. Si se repite la misma
`idempotency_key` con el mismo cuerpo, responde `duplicado: true` y no agrega
lecturas; si el cuerpo cambia, responde `409`.

Desde n8n ejecutándose en Windows, la URL es `http://127.0.0.1:8000/api/ingesta`.
Si n8n corre en Docker, usa `http://host.docker.internal:8000/api/ingesta`.

Hay un workflow listo para importar en `n8n/SATQ - Ingesta manual.json`
(instrucciones en `n8n/README.md`). Envía lecturas simuladas y, si el nivel es
alto o crítico, crea la alerta mediante `POST /api/alertas`.

### Creación de alertas desde n8n

Después de una ingesta con `alerta_requerida: true`, n8n puede llamar a
`POST /api/alertas` con la misma clave `X-API-Key`:

```json
{
  "quebrada": "quirio",
  "fuente": "n8n-demo",
  "idempotency_key": "demo-2026-10-29-01-alerta"
}
```

La respuesta `201` incluye la alerta creada, por ejemplo `AL-0008`. Si se repite
la misma clave, responde `200` con `duplicado: true` y no crea otra. Si la
quebrada ya tiene una alerta activa, responde `200` con `creada: false` y
`motivo: "alerta_activa"`. Si el nivel no es alto ni crítico, responde `409`.

### Observabilidad

- `/health` (en ambos servidores) indica si el servicio está sano; en modo
  PostgreSQL devuelve `503` si la base no responde.
- `/api/metricas` (solo `app.py`) devuelve peticiones, errores y tiempos.
- Los logs son una línea JSON por petición; el nivel se ajusta con
  `SATQ_LOG_LEVEL`.
- Detalle en `docs/observabilidad.md`.

---

## Documentación

- `docs/observabilidad.md` — qué se registra y cómo consultarlo.
- `docs/mensajeria.md` — canales SMS, variables de entorno y controles de costo.
- `docs/suscripcion.md` — suscripción por zona, quebrada más cercana y despacho.
- `satqito/README.md` — cómo crear y ejecutar el bot Satqito.
- `n8n/README.md` — cómo importar y ejecutar el workflow de ingesta.
