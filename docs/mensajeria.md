# Mensajería SMS

SATQ Digital usa **SMS como canal principal** porque el destinatario no necesita
datos móviles ni WiFi: solo cobertura celular. El envío real se activa con
variables de entorno; sin ellas, el sistema funciona en modo **simulado** para
desarrollo, pruebas y CI.

## Modos

| `SATQ_SMS_MODO` | Comportamiento |
|---|---|
| `simulado` (por defecto) | Registra la comunicación sin enviar nada |
| `real` | Envía SMS con el proveedor configurado |

## Proveedores

### Twilio

```powershell
$env:SATQ_SMS_MODO="real"
$env:SATQ_SMS_PROVEEDOR="twilio"
$env:SATQ_TWILIO_SID="AC..."
$env:SATQ_TWILIO_TOKEN="..."
$env:SATQ_TWILIO_FROM="+1..."
$env:SATQ_SMS_DESTINO="+51..."
$env:SATQ_SMS_MAX_ENVIOS="10"
```

- Usa la API REST de Twilio con `urllib` (sin dependencias nuevas).
- En Perú se admite **long code internacional**.
- No hay SMS bidireccional y el sender ID puede sobrescribirse.
- El número destino debe estar verificado en cuentas trial.

### Vonage

```powershell
$env:SATQ_SMS_MODO="real"
$env:SATQ_SMS_PROVEEDOR="vonage"
$env:SATQ_VONAGE_API_KEY="..."
$env:SATQ_VONAGE_API_SECRET="..."
$env:SATQ_VONAGE_FROM="SATQ"
$env:SATQ_SMS_DESTINO="+51..."
$env:SATQ_SMS_MAX_ENVIOS="10"
```

- Usa la API `rest.nexmo.com/sms/json`.
- Verifica cobertura, remitente y tarifa para Perú en el dashboard de Vonage.

### Infobip

```powershell
$env:SATQ_SMS_MODO="real"
$env:SATQ_SMS_PROVEEDOR="infobip"
$env:SATQ_INFOBIP_API_KEY="..."
$env:SATQ_INFOBIP_BASE_URL="https://xxxxx.api.infobip.com"
$env:SATQ_INFOBIP_FROM="SATQ"
$env:SATQ_SMS_DESTINO="+51..."
$env:SATQ_SMS_MAX_ENVIOS="5"
```

- Usa `POST {base_url}/sms/2/text/advanced` con `Authorization: App <API_KEY>`.
- El plan trial suele incluir **15 SMS gratis**; usa un tope de 5 para la demo.
- Verifica en el dashboard el remitente permitido y la cobertura para Perú.

## Controles de costo

- **Tope de envíos:** `SATQ_SMS_MAX_ENVIOS` (por proceso). Al alcanzarlo, los
  siguientes envíos quedan como `fallido` con el motivo "límite alcanzado".
- **Destino único:** solo se envía a `SATQ_SMS_DESTINO`; no se aceptan números
  arbitrarios desde la interfaz.
- **Idempotencia:** una misma combinación quebrada + canal + plantilla no se
  envía dos veces en la misma sesión.
- **Mensajes de un solo segmento:** las plantillas son cortas para evitar
  múltiples cobros.
- **Pruebas sin red:** los tests usan un canal falso y nunca envían SMS.

## Qué se guarda

Cada comunicación registra:

- estado (`enviado`, `fallido`, `pendiente`)
- proveedor (`twilio`, `vonage`, `simulación`)
- id externo del proveedor
- error (si falló)
- intentos
- destino enmascarado (por ejemplo `+51****1234`)
- clave de idempotencia

## Interfaz

- Si `SATQ_SMS_MODO=simulado`, la interfaz indica "Solo simulación".
- Si `SATQ_SMS_MODO=real` y el proveedor está configurado, indica "SMS real".
- Si el envío falla, la alerta **no se bloquea**: se registra el error y se
  muestra en el historial.

## Límites y advertencias

- El servidor necesita internet para llamar al proveedor.
- El SMS puede demorar o fallar; no hay garantía de entrega.
- No se debe usar para decisiones de emergencia ni como canal oficial.
- En producción se recomienda un agregador local o una pasarela GSM con
  redundancia.
- Nunca guardes credenciales en el repositorio.
