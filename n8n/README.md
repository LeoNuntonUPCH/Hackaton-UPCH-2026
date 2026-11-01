# n8n · automatización de ingesta (demostración)

Workflow **`SATQ - Ingesta manual.json`**: envía lecturas de lluvia simuladas al
SATQ y, si el nivel resultante es alto o crítico, crea una alerta. Forma parte de
la demostración: **no** se conecta a SENAMHI ni a INAIGEM y no envía mensajes.

## Requisitos

1. SATQ corriendo con la misma clave que usa el workflow:
   ```powershell
   $env:SATQ_INGESTA_API_KEY="satq-demo-local"
   python -m uvicorn app:app --host 127.0.0.1 --port 8000
   ```
2. n8n instalado y funcionando en <http://localhost:5678>.

## Importar el workflow

1. Abre n8n → **Workflows** → **Import from File** (o menú **⋯**).
2. Selecciona `n8n/SATQ - Ingesta manual.json`.
3. Revisa la URL de los nodos HTTP:
   - n8n en Windows → `http://127.0.0.1:8000`
   - n8n en Docker → `http://host.docker.internal:8000`
4. Ejecuta con **Test workflow**.

## Qué hace

| Nodo | Acción |
|---|---|
| When clicking 'Execute workflow' | Disparo manual |
| Code in JavaScript | Prepara lecturas simuladas para `quirio` (`mm_h: 100.0`) |
| HTTP Request | `POST /api/ingesta` con `X-API-Key` |
| If | ¿`alerta_requerida` es `true`? |
| HTTP Request1 | `POST /api/alertas` con la misma `X-API-Key` |
| Sin Alerta | Rama cuando el nivel no exige alerta |

## Coherencia con la API

- La `X-API-Key` del workflow es `satq-demo-local` y **debe coincidir** con
  `SATQ_INGESTA_API_KEY` del servidor; si no, responde `401`.
- El body de ingesta es `JSON.stringify($json)` del nodo Code: incluye
  `quebrada`, `fuente`, `idempotency_key` y `lecturas` (`mm_h` entre 0 y 500).
- El nodo de alertas reutiliza `quebrada`, `fuente` e `idempotency_key` de la
  respuesta de ingesta, que el API devuelve.
- La `idempotency_key` es **fija** (`demo-quirio-001`): la primera ejecución
  inserta lecturas; las siguientes responden `duplicado: true` y no cambian nada.
  Para repetir la demo con efectos nuevos, cámbiala por una dinámica, por ejemplo:
  ```js
  idempotency_key: `demo-${new Date().toISOString()}`
  ```

## Qué comprobar

- `POST /api/ingesta` responde con `nivel`, `acumulado_mm` y `alerta_requerida`.
- Si `alerta_requerida` es `true`, se crea una alerta `pendiente` visible en
  `/alertas`.
- Reejecutar con la misma `idempotency_key` no duplica lecturas.
- En modo `SATQ_DB=postgres`, lecturas y alertas **persisten** al reiniciar.

## Límites explícitos

- Los datos son **sintéticos**: no provienen de ninguna estación real.
- No hay envío de WhatsApp/SMS.
- Este workflow no demuestra una integración oficial, solo el contrato de
  ingesta que una integración futura podría usar.
