# Observabilidad

Qué se registra y cómo consultarlo. Todo usa la librería estándar: no hay
dependencias nuevas ni servicios externos, y funciona sin internet.

## 1. Logs estructurados

Cada petición se registra como **una línea JSON** en la salida del servidor:

```json
{"evento": "peticion", "metodo": "GET", "ruta": "/dashboard", "estado": 200, "ms": 12.4}
```

- `estado >= 500` → nivel `error`
- `estado >= 400` → nivel `warning`
- resto → nivel `info`

El nivel mínimo se controla con la variable de entorno `SATQ_LOG_LEVEL`
(por defecto `INFO`):

```powershell
$env:SATQ_LOG_LEVEL="DEBUG"
```

## 2. Métricas en memoria

`GET /api/metricas` (solo con `app.py`) devuelve:

| Campo | Qué mide |
|---|---|
| `peticiones_total` | Peticiones atendidas desde el arranque |
| `errores_5xx` | Respuestas con error de servidor |
| `peticiones_por_ruta` | Conteo por método y ruta |
| `duracion_promedio_ms` | Tiempo medio de respuesta |
| `duracion_max_ms` | Peor tiempo observado |
| `ultima_peticion` | Método, ruta, estado y duración de la última |
| `uptime_s` | Segundos desde el arranque |

Los contadores viven en memoria: se reinician con el proceso y no se guardan en
PostgreSQL.

## 3. Salud del servicio

`GET /health` responde en ambos servidores:

```json
{
  "estado": "ok",
  "base_datos": {"modo": "memoria", "conectada": null},
  "uptime_s": 7.0,
  "peticiones_total": 0,
  "errores_5xx": 0
}
```

- `estado: "ok"` → `200`.
- En modo PostgreSQL, si la base no responde → `estado: "degradado"` y `503`.

## 4. Límites

- No hay integración con Sentry, Grafana ni similares.
- `servidor_demo.py` solo expone `/health` (no tiene API de métricas).
- Las métricas no sustituyen una monitorización de producción.
