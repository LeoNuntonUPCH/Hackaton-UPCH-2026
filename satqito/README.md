# Satqito · bot de Telegram

Bot independiente de SATQ Digital. Sirve para:
- saludar y consultar el estado actual del país,
- explicar la finalidad del sistema,
- registrar una suscripción por SMS,
- verificar el teléfono con un código de 4 dígitos,
- consultar el estado y darse de baja.

No modifica alertas ni datos de riesgo. Solo **lee** y **registra** suscripciones a través de la API.

## Requisitos

1. SATQ corriendo en `http://127.0.0.1:8000`.
2. API key para el bot: `SATQ_BOT_API_KEY`.
3. Token de BotFather: `SATQ_TELEGRAM_BOT_TOKEN`.

## Crear el bot

1. En Telegram, abre **@BotFather**.
2. `/newbot`.
3. Nombre: **Satqito**.
4. Username terminado en `bot`, por ejemplo **SatqitoAlertasBot**.
5. Copia el token.

## Variables de entorno

```powershell
$env:SATQ_BOT_API_KEY="clave-interna-del-bot"
$env:SATQ_TELEGRAM_BOT_TOKEN="123456:ABC..."
$env:SATQ_API_URL="http://127.0.0.1:8000"
```

En el servidor de SATQ también debe existir la misma `SATQ_BOT_API_KEY`:

```powershell
$env:SATQ_BOT_API_KEY="clave-interna-del-bot"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

## Arrancar Satqito

```powershell
python -m satqito
```

## Flujo

```
/start
  → saludo + estado del país + aviso de demostración
  → ¿quieres recibir alertas?
  → teléfono (+51...)
  → compartir ubicación
  → quebrada más cercana
  → SMS con código de 4 dígitos
  → verificación
  → suscripción registrada
  → /estado · /probar · /baja · /ayuda
```

`/probar` envía un SMS de prueba **solo al número del chat**, no a todos los
suscriptores. Las alertas por área se envían a los suscriptores de la quebrada.

## Lanzador para la demo

1. Doble clic en `iniciar_demo.bat` (archivo local, no se sube al repo).
2. Comparte <https://t.me/SatqitoAlertasBot>.

Con `SATQ_SMS_PERMITIR_ABIERTOS=1` cualquier persona puede registrarse; el tope
`SATQ_SMS_MAX_ENVIOS` controla el costo.

## Notas

- Las alertas se envían por **SMS**, no por Telegram. Telegram solo se usa para el registro y la consulta.
- No hace falta crear grupos: el bot funciona por chat directo.
- El teléfono debe estar permitido en `SATQ_SMS_DESTINOS_PERMITIDOS` para enviar SMS reales.
- Satqito no reemplaza a las autoridades ni emite alertas oficiales.
- No guardes el token en el repositorio.
