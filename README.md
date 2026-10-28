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
├── app.py                 Aplicación FastAPI: rutas + API JSON documentada
├── servidor_demo.py       Servidor de respaldo, sin dependencias externas
├── pruebas_flujo.py       Pruebas de los flujos interactivos
├── requirements.txt
├── iniciar.bat
└── satq/
    ├── motor.py           Motor de clasificación de riesgo  ← el corazón
    ├── datos.py           Escenario simulado (24 quebradas, 7 alertas)
    ├── estado.py          Estado en memoria (hace de PostgreSQL)
    ├── graficos.py        Gráfico y mapa en SVG, generados en el servidor
    ├── vistas.py          Qué datos ve cada pantalla
    ├── plantillas.py      Entorno Jinja2
    ├── templates/         10 plantillas HTML
    └── static/css/        Una hoja de estilos
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
| Panel web | Streamlit o React | HTML/CSS servido por FastAPI |
| Base de datos | PostgreSQL | Estado en memoria |
| Automatización | n8n | No implementada |
| Mensajería | API WhatsApp / SMS | Simulada, sin envío |
| Fuentes de datos | SENAMHI · INAIGEM | No conectadas; series sintéticas |

---

## Sobre los datos

Las series de lluvia son sintéticas y **deterministas**: se generan con una
semilla fija, de modo que el escenario es idéntico en cada ejecución y la
demostración es reproducible. El episodio simulado empieza seis horas antes del
momento mostrado (26 oct 2026, 10:35 PET), por eso el acumulado móvil sube desde
casi cero.

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

---

## API JSON (solo con `app.py`)

| Endpoint | Qué devuelve |
|---|---|
| `GET /api/resumen` | Conteos por nivel y por estado de gestión |
| `GET /api/quebradas` | Las 24 quebradas con acumulado y nivel |
| `GET /api/quebradas/{codigo}` | Serie de acumulado y evaluación |
| `GET /api/alertas` | Alertas del escenario |
| `GET /api/evaluar?acumulado_mm=42` | Aplica el motor a un valor cualquiera |
| `POST /api/reiniciar` | Devuelve el escenario a su punto inicial |

Documentación interactiva en `/docs`.
