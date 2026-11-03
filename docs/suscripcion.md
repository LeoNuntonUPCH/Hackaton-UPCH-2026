# Suscripción comunitaria

Permite que un vecino registre su teléfono y su zona para recibir avisos de la
quebrada más cercana. Es una demostración: no sustituye a las autoridades ni a
los sistemas oficiales.

## Flujo

```
Vecino completa el formulario (/suscripcion)
        │
        ├── Teléfono + nombre (opcional)
        ├── Zona elegida o ubicación del navegador
        └── Consentimiento explícito
        │
        ▼
Se guarda el suscriptor (memoria o PostgreSQL)
        │
        ▼
Si hay alerta alta/crítica, se despacha a los suscriptores de esa quebrada
        │
        ▼
Cada envío queda registrado con estado, proveedor, error e idempotencia
```

## Cómo se elige la quebrada

- Si el navegador comparte ubicación, se calcula la **quebrada más cercana** con
  la fórmula de Haversine sobre las coordenadas de las quebradas.
- Si no hay ubicación, se usa la **zona seleccionada** en el formulario.

## Suscripción desde Satqito (Telegram)

El bot `satqito/` puede registrar suscriptores con `origen=telegram`. El flujo es:
teléfono → ubicación → quebrada más cercana → **código SMS de 4 dígitos** →
verificación. Hasta no verificar el código, la suscripción no se considera
confirmada.

El bot no modifica alertas ni datos de riesgo: solo consulta y registra.

## Envío automático

Por defecto el despacho es **manual**, desde el botón "Enviar a suscriptores" de
`/suscripcion`. Para activar el envío automático cuando n8n crea una alerta:

```powershell
$env:SATQ_ALERTAS_AUTO="1"
```

Solo se despacha cuando se crea una alerta nueva (no en duplicados ni cuando ya
existe una alerta activa).

## Seguridad y costos

- **Consentimiento obligatorio:** sin la casilla no se registra.
- **Lista blanca de destinos:** en modo real solo se envía a números incluidos en
  `SATQ_SMS_DESTINOS_PERMITIDOS` (o al `SATQ_SMS_DESTINO`).
- **Modo abierto para la demo:** `SATQ_SMS_PERMITIR_ABIERTOS=1` permite registrar
  cualquier número, con tope `SATQ_SMS_MAX_ENVIOS` para controlar el costo.
- **Tope de envíos:** `SATQ_SMS_MAX_ENVIOS`.
- **Idempotencia:** una alerta + canal + plantilla + teléfono no se repite.
- **Baja:** botón "Dar de baja" en la lista de suscriptores.
- **Privacidad:** el teléfono se muestra enmascarado (`+51****1234`).

## SMS de prueba por usuario

Satqito tiene el comando `/probar`, que envía un SMS **solo al número del chat
que lo solicita**. Así el jurado puede comprobar la recepción sin alertar a todos
los suscriptores de la quebrada.

## Variables relacionadas

```powershell
$env:SATQ_SMS_MODO="real"
$env:SATQ_SMS_PROVEEDOR="infobip"
$env:SATQ_SMS_DESTINOS_PERMITIDOS="+51999888777,+51999777666"
$env:SATQ_ALERTAS_AUTO="1"
```

## Límites

- No hay SMS bidireccional: la suscripción se hace por la web (o, en el futuro,
  por un bot de Telegram).
- El aviso no debe usarse para decisiones de emergencia.
- El texto de la plantilla debe revisarse localmente antes de un uso real.
- La entrega SMS no está garantizada.
