# Protocolo de reproducción: Huaycoloro 2, marzo de 2023

SATQ Digital es un prototipo con datos y alertas simulados. No usar para decisiones de emergencia. Este protocolo mide el comportamiento retrospectivo de tres reglas de lluvia; no reconstruye alertas operativas del SATQ ni calibra los umbrales con esta muestra.

## Reglas fijadas para el contraste

1. **Datos y periodo.** Lluvia incremental observada, en mm por intervalo de una hora. Usar marzo para obtener el arrastre anterior al corte; evaluar del 12/03 a las 00:00 al 19/03 a las 00:00 (extremo final excluido), en PET (UTC−5). El contraste de Ñaña usa la marca publicada como fin de hora PET **bajo supuesto**; repetir como inicio de hora (+1 h), y ambos casos si la hora publicada fuera UTC (−5 h para llevarla a PET, luego +1 h si marca el inicio). El archivo normalizado conserva la hora publicada sin asignarle zona. Una evaluación local exige confirmar zona, intervalo y representatividad antes de interpretar puntajes.
2. **Lluvia móvil.** Para cada fin de hora `t`, sumar seis intervalos consecutivos que terminan en `t`, incluida esa hora. Una hora ausente, `S/D` o inválida invalida la ventana; no imputar ni convertir totales diarios. Revisar duplicados por estación y marca de tiempo; no confundir valores iguales con claves duplicadas. Documentar y conservar valores sospechosos separados de cualquier serie filtrada.
3. **Alertas candidatas.** Evaluar por separado `20`, `30` y `40 mm/6 h`. Emitir una alerta en `t` solo si el acumulado es `>= umbral` y el acumulado de `t−1 h` era válido y `< umbral`. La permanencia por encima del umbral no crea nuevas alertas. Si falta una de las dos ventanas, el cruce no es evaluable; no inferir un cruce al recuperar el dato. En cada umbral reportar cuántas horas se pudieron evaluar. Para asignar un resultado a una alerta se requiere disponer de las seis horas posteriores del inventario: con el corte actual se consideran las alertas anteriores al 18/03 18:00 PET. Las horas posteriores se excluyen del cómputo de alertas y se incluyen en la descripción de cobertura de lluvia.
4. **Eventos.** Usar las horas locales de detección de Huaycoloro 2, no las horas administrativas de reporte ni detecciones de otra estación. Conservar la vista provisional de cuatro episodios, agrupando detecciones de la misma estación con brecha `<6 h` y tomando la primera hora. Repetir con cinco detecciones sin agrupar y con la detección de las 15:28:38 asignada al 17/03 según la portada discordante. Ninguna variante resuelve por sí sola qué ocurrió. Si no se puede evaluar alguna hora de alerta candidata en `[evento−6 h, evento]`, identificar el evento como indeterminado antes de contar H/M; si ello altera la asignación de una alerta, no clasificar esa alerta como falsa.
5. **Asociación y métricas.** Emparejar solo Huaycoloro 2, uno a uno, por orden cronológico de evento. Para cada evento elegir la alerta elegible más antigua con anticipación de `0–360` minutos inclusive (`satq.validacion.evaluar_eventos`). H = pares, M = eventos evaluables no emparejados, F = alertas evaluables no emparejadas *respecto al inventario disponible*. Informar POD=`H/(H+M)`, FAR=`F/(H+F)`, CSI=`H/(H+M+F)`; si el denominador es cero, el resultado es indefinido. No extrapolar F a días sin vigilancia confirmada. Conservar los casos sin dato y los bordes fuera de H/M/F, y declarar la cobertura del inventario.

## Revisión de las detecciones

Se verificó la fecha y hora de **detección** en el campo interno de los reportes IGP accesibles mediante el índice web. En Chrome, el enlace antiguo del reporte rotulado 17/03 redirigió al nuevo portal, que muestra monitoreo en tiempo real. No se recuperaron copias binarias de los PDF ni se cambió el [inventario previo de cinco registros](../datos/validacion/eventos_huaycoloro2_20230312_18.csv).

| Detección (PET) | Evidencia y decisión |
| --- | --- |
| 12/03 17:43:00 | [IGP, p. 1](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_12_03_2023_HL2.pdf): el título y el campo **Estación** coinciden en Huaycoloro 2; el subtítulo dice Huaycoloro 1. INDECI, p. 1, sitúa la activación de varias quebradas, incluida Huaycoloro 2, alrededor de las 17:44. Se conserva la hora IGP. |
| 14/03 15:24:33 | [IGP, p. 1](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_14_03_2023_HL2.pdf): mismo error de subtítulo; el campo **Estación** y el título dicen Huaycoloro 2. INDECI, p. 24, anota 15:26 en la columna **Hora del reporte**. No se sustituye la hora de detección. |
| 15/03 14:44:19 | [IGP, enlace del inventario](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_15_03_2023_HL2.pdf): el enlace redirige al nuevo portal y no se pudo cotejar de nuevo este segundo exacto. Se conserva la transcripción previa. INDECI, p. 20, registra Huaycoloro 2 a las 15:39 como **Hora del reporte**, lo que respalda actividad ese día, pero no confirma esta hora de detección. |
| 15/03 15:28:38 **o** 17/03 15:28:38 | [IGP, p. 1](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_17_03_2023_HL2.pdf): portada y nombre de archivo dicen 17/03; **Fecha** interna dice 15/03. El [reporte compañero de Huaycoloro 1](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_17_03_2023_HL1.pdf) sí da 17/03 tanto en portada como en el campo interno, a las 14:26:28, pero es otra estación y no resuelve la fecha de Huaycoloro 2. |
| 18/03 17:54:46 | [IGP, p. 1](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_18_03_2023_HL2.pdf): fecha, hora local y estación Huaycoloro 2 coinciden con el inventario. |

Fuente independiente: [INDECI, Informe de Emergencia 637, pp. 1, 20 y 24](https://portal.indeci.gob.pe/wp-content/uploads/2023/03/INFORME-DE-EMERGENCIA-N%C2%BA-637-21MAR2023-LLUVIAS-INTENSAS-EN-EL-DEPARTAMENTO-DE-LIMA-13-DEE.pdf). Si la fecha interna 15/03 es correcta, las dos detecciones están a **44 min 19 s** en el mismo punto. Agruparlas es una convención de evaluación: los reportes no dan evidencia continua del flujo ni un fin de episodio que confirme que fueron uno solo o dos. Si la portada es correcta, la brecha es de dos días y no corresponde agrupar. Por eso se conservan los tres escenarios. No se conoce la completitud del inventario de Huaycoloro 2 ni su bitácora de disponibilidad.

## Resultado: proxy con Ñaña automática 111290

El [visor de SENAMHI](https://www.senamhi.gob.pe/mapas/mapa-estaciones-ms/map_red_graf.php?cod=111290) muestra lluvia observada de marzo de 2023 en Ñaña, a **5,5 km** en línea recta de la referencia del Radio Observatorio de Jicamarca. El [boletín CHIRILU](https://www.senamhi.gob.pe/load/file/02231SENA-70.pdf) ubica Ñaña en el Rímac bajo; el [Plan Maestro de la ANA, p. 60](https://repositorio.ana.gob.pe/bitstream/handle/20.500.12543/637/ANA0000423.pdf?isAllowed=y&sequence=1) distingue al Huaycoloro como afluente. La cercanía al observatorio no demuestra que el pluviómetro mida lluvia en el área aportante aguas arriba de la detección. Tampoco se comprobó una relación de lluvia entre Ñaña y esa área. Se usa como **proxy observado cercano**, sin validación local de Huaycoloro.

En la semana, hubo **155/168** acumulados válidos y **147/162** horas con cruce evaluable tras excluir las últimas 6 h por borde del inventario. Los tres faltantes del corte invalidan 13 acumulados y 15 posibles cruces, pero todas las horas de alerta candidatas en las ventanas de los eventos del inventario son evaluables. El máximo de seis horas fue **9,2 mm/6 h** (14/03, 23:00 si la hora publicada es PET de fin de intervalo); no se observó un cruce en las horas evaluables.

| Inventario | Umbral (mm/6 h) | H | M | F | POD | FAR | CSI |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 4 episodios provisionales | 20, 30, 40 (cada uno) | 0 | 4 | 0 | 0 | Indefinido | 0 |
| 5 detecciones, fecha interna 15/03 | 20, 30, 40 (cada uno) | 0 | 5 | 0 | 0 | Indefinido | 0 |
| 5 detecciones, fecha de portada 17/03 | 20, 30, 40 (cada uno) | 0 | 5 | 0 | 0 | Indefinido | 0 |

Los cuatro supuestos de hora dan esos mismos conteos. La tabla de [36 combinaciones](../datos/validacion/diagnostico_proxy_senamhi_nana_pod_far_csi_20230312_18.csv) y el [detalle por evento](../datos/validacion/ventanas_evento_proxy_senamhi_nana_20230312_18.csv) conservan la cobertura y el escenario. Un máximo inferior al umbral en esta serie no demuestra que haya llovido poco en la cabecera; tampoco prueba que el SATQ hubiera omitido activaciones en operación.

## Reproducir las métricas del proxy

Desde `Hackaton-UPCH-2026`, ejecutar el siguiente bloque en Python 3.11 o posterior. Lee los CSV y comprueba que la cuadrícula horaria y las ventanas de los eventos son evaluables para este caso. No modifica archivos. `None` en la salida equivale a **indefinido**.

```python
import csv
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from satq.validacion import AlertaEmitida, cargar_eventos_csv, evaluar_eventos

p = Path("datos/validacion")
hora = timedelta(hours=1)
pet = timezone(-5 * hora)
inicio = datetime(2023, 3, 12, tzinfo=pet)
horas = [inicio + i * hora for i in range(168)]
with (p / "observaciones_horarias_senamhi_nana_111290_202303.csv").open(
    encoding="utf-8", newline=""
) as f:
    lluvia = {}
    for fila in csv.DictReader(f):
        t = datetime.fromisoformat(fila["instante_publicado_sin_zona"])
        assert t not in lluvia
        valor = fila["precipitacion_mm_intervalo_1h"]
        lluvia[t] = Decimal(valor) if valor else None
assert sorted(lluvia) == [datetime(2023, 3, 1) + i * hora for i in range(744)]
grupos = cargar_eventos_csv(p / "episodios_candidatos_huaycoloro2_20230312_18.csv")
registros = cargar_eventos_csv(p / "eventos_huaycoloro2_20230312_18.csv")
portada = [replace(e, instante=e.instante + timedelta(days=2))
           if e.instante.astimezone(pet).isoformat() == "2023-03-15T15:28:38-05:00"
           else e for e in registros]

for nombre, ajuste in (("PET_fin", 0), ("PET_inicio", 1), ("UTC_fin", -5), ("UTC_inicio", -4)):
    serie = {t.replace(tzinfo=pet) + ajuste * hora: mm for t, mm in lluvia.items()}
    def suma6(t):
        valores = [serie.get(t - i * hora) for i in range(6)]
        return None if None in valores else sum(valores)

    acumulados = {t: suma6(t) for t in [inicio - hora, *horas]}
    cruces = {t for t in horas[:-6]
              if acumulados[t] is not None and acumulados[t - hora] is not None}
    validos = [acumulados[t] for t in horas if acumulados[t] is not None]
    print(nombre, "ventanas válidas:", len(validos), "máximo:", max(validos),
          "horas de cruce evaluables:", len(cruces))
    for inventario, eventos in (("4 agrupados", grupos), ("5 fecha interna", registros),
                                 ("5 portada", portada)):
        for e in eventos:
            candidatos = {t for t in horas[:-6] if e.instante - 6 * hora <= t <= e.instante}
            assert len(candidatos) == 6 and candidatos <= cruces
        for umbral in (20, 30, 40):
            alertas = [AlertaEmitida("Huaycoloro 2", t) for t in sorted(cruces)
                       if acumulados[t - hora] < umbral <= acumulados[t]]
            print(inventario, umbral, evaluar_eventos(alertas, eventos, 360))
```

### Seguimiento de fuentes y gestión de solicitudes

La búsqueda pública adicional en Chrome del 07/11/2026 no encontró una serie
subdiaria observada representativa de la cuenca aportante ni la bitácora IGP
de disponibilidad/detecciones que resuelva la discrepancia del 15/17. El
seguimiento, los canales oficiales consultados y el borrador local no enviado
para solicitar ambos insumos están registrados en el [expediente de
validación](../datos/validacion/README.md#seguimiento-de-búsqueda-pública-en-chrome--07112026)
y en [`datos/validacion/solicitud_insumos_huaycoloro2_borrador.md`](../datos/validacion/solicitud_insumos_huaycoloro2_borrador.md).
No se transmitió el borrador a institución alguna.

## Acceso comprobado y siguiente paso

En Chrome se consultaron el visor SENAMHI de Lima, Ñaña automática, el portal del IGP y el histórico del COES. El buscador SENAMHI no mostró coincidencias por Huaycoloro, Jicamarca, Chaclla o Cajamarquilla. Autisha (`111077`), Arahuay (`111057`) y Santa Eulalia (`111086`) aparecen como estaciones pluviométricas convencionales; esa ficha no acredita una serie subdiaria. Huachipa automática (`212607`) figura como hidrológica y, al abrir su tabla, pidió verificación antirobot; no se completó. El [histórico del COES](https://sicoes.coes.org.pe/Portal/Operacion/HistoricoHidrologia/) permite seleccionar caudal o volumen, sin opción de precipitación. El [sistema IGP de detección](https://www.gob.pe/41855-centro-de-monitoreo-de-deslizamientos-y-huaicos-cendehua) describe cámaras y sensores de continuidad y nivel; su hora de activación no es una medición de lluvia. El [radar SOPHy](https://www.igp.gob.pe/proyectos/desarrollo-tecnologico/radar-meteorologico/acercade) es otra tecnología de observación, pero la página consultada no acredita una serie pública calibrada para este corte. No se iniciaron sesiones, resolvieron CAPTCHA, instalaron plugins ni enviaron mensajes.

Para la evaluación local falta una serie de pluviómetro dentro del área aportante aguas arriba de Huaycoloro 2, o un conjunto de estaciones cuya representatividad se justifique con la delimitación de cuenca, elevación y comparación de tormentas. Se requiere cobertura del 12–18/03, más margen antes y después, con zona, significado de la marca horaria, calidad y licencia. También falta el inventario de detecciones y de tiempo operativo del IGP para resolver el 15/17 y confirmar los periodos sin evento. Con ambos insumos disponibles, se estiman **4–8 horas de trabajo** para comprobar ubicación y metadatos, verificar huecos, curar eventos y ejecutar el protocolo; el plazo de obtención de los insumos es desconocido. Para medir desempeño operativo haría falta además una bitácora real de emisión de alertas SATQ; el prototipo no la tiene para marzo de 2023.
