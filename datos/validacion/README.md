# Evidencia de lluvia y eventos: Huaycoloro 2, 12–18/03/2023

El [protocolo y revisión de cronología](../../docs/protocolo_huaycoloro2_202303.md) incluye un contraste nuevo con **lluvia horaria observada de Ñaña**. Es un proxy del valle del Rímac; sigue sin haber una serie pluviométrica representativa de la cuenca aportante de Huaycoloro 2. El SATQ de demostración usa datos y alertas simulados; no usar para decisiones de emergencia.

## Serie horaria observada: Ñaña automática (111290)

- **Origen y acceso:** SENAMHI / DRD, [visor de Ñaña](https://www.senamhi.gob.pe/mapas/mapa-estaciones-ms/map_red_graf.php?cod=111290), pestaña **Tabla**, mes **2023-03**, consultada en Chrome el 07/11/2026 sin iniciar sesión, pagar ni resolver CAPTCHA. Es una vía distinta de WIS 2.0; no se presume que los identificadores WIGOS y del visor sean intercambiables. El botón **Exportar a CSV** no dejó un archivo verificable en esta sesión. Se conservó una captura de las tres columnas de lluvia, comprobada contra todas las celdas visibles, con fechas, horas, cifras y `S/D` tal como aparecen. No se presenta como descarga binaria del portal.
- **Ubicación:** Lurigancho, Lima; estación meteorológica automática a 553 m s. n. m. El visor muestra `11°59′14.94″ S`, `76°50′30.94″ W` (`-11.9874833, -76.8419278`). Distancia en línea recta: 5,5 km a la referencia del Radio Observatorio de Jicamarca y 12,5 km al punto demo. [SENAMHI sitúa Ñaña en el Rímac bajo](https://www.senamhi.gob.pe/load/file/02231SENA-70.pdf); no se acreditó que represente la lluvia en el área que drena a Huaycoloro 2.
- **Cobertura y unidades:** 01/03/2023 00:00–31/03/2023 23:00, 744 marcas horarias, 739 valores de lluvia numéricos, cero horas ausentes y cero claves repetidas. La unidad publicada es `mm/hora`; para el contraste cada valor se trata como mm durante su intervalo de una hora. La zona y el inicio/fin de intervalo no constan en la tabla; la serie normalizada guarda la hora sin zona. La reproducción ensaya PET y UTC, ambos con marcas de inicio y de fin.
- **Calidad y licencia:** datos sin control de calidad según la fuente. Cinco `S/D` en hora publicada: 03/03 06:00, 05/03 23:00, 12/03 23:00, 13/03 00:00 y 13/03 23:00. El valor aislado de 35,6 mm/h del 09/03 04:00 está fuera del corte y se conserva sin certificar. El 14/03 18:00 y 19:00 repite 2,1 mm/h con las demás columnas iguales; son marcas distintas y no se deduplicaron. La licencia de reutilización no está declarada en la ficha consultada; se conserva la atribución y no se aplica la licencia del conjunto GBON/RBON a esta fuente.

| Archivo | Contenido | SHA-256 |
| --- | --- | --- |
| [Captura de la tabla](captura_tabla_senamhi_nana_111290_202303.csv) | 744 filas; fecha y hora publicadas y texto de precipitación | `99905b90c5865f5c5c2cd7dff02cb2c61e40129ac5e4e98b5282e7324995134e` |
| [CSV normalizado](observaciones_horarias_senamhi_nana_111290_202303.csv) | ISO 8601 sin zona, `S/D` como celda vacía y procedencia por fila | `6b0c464181ad4590aadc9bda3313b75a75d0aabf976161a41df4567c01bea81b` |
| [Métricas proxy](diagnostico_proxy_senamhi_nana_pod_far_csi_20230312_18.csv) | 3 umbrales × 3 inventarios × 4 interpretaciones de hora | `2bd8117cff15976ccfdb650c5b21c36b073fe482f82dc35d9aeafb01f914101a` |
| [Ventanas por evento](ventanas_evento_proxy_senamhi_nana_20230312_18.csv) | Supuesto PET fin de hora, cobertura de anticipación y máximo acumulado para cada detección | `00a41d7a8791b36367b8aedfb95d68cd71b81fa03a5e164b7c4cd3cece33ff1f` |

El CSV normalizado no se carga directamente con `cargar_lecturas_csv`, que requiere una marca con zona horaria. El protocolo documenta la lectura explícita de la hora publicada bajo cada supuesto. Los archivos anteriores a este contraste se conservaron.

## Expediente previo

Se amplió el caso piloto a cinco reportes de activación de la estación
Huaycoloro 2 del IGP. Las dos consultas de precipitación horaria cubren 168
horas cada una y se hicieron
el 2026-11-07 mediante la API pública de Open-Meteo, modelo ECMWF IFS, zona
`America/Lima` (UTC−5), variable `precipitation` en mm por hora.

## Consultas espaciales y temporales

| Punto de consulta | Coordenadas de entrada | Celda devuelta | Elevación | Consulta |
| --- | --- | --- | ---: | --- |
| Demo SATQ | `-11.95, -76.95` | `-11.915641, -76.92377` | 798 m | [API](https://archive-api.open-meteo.com/v1/archive?latitude=-11.95&longitude=-76.95&start_date=2023-03-12&end_date=2023-03-18&hourly=precipitation&timezone=America%2FLima&models=ecmwf_ifs) |
| Referencia IGP/Jicamarca | `-11.9523176, -76.8779755` | `-11.98594, -76.91202` | 496 m | [API](https://archive-api.open-meteo.com/v1/archive?latitude=-11.9523176&longitude=-76.8779755&start_date=2023-03-12&end_date=2023-03-18&hourly=precipitation&timezone=America%2FLima&models=ecmwf_ifs) |

La ubicación IGP es la coordenada pública del Radio Observatorio de Jicamarca,
próximo a la referencia del reporte de activación, no la coordenada levantada de
la estación del puente. El producto tiene grilla nominal de alrededor de 9 km;
las celdas devueltas no son pluviómetros ni mediciones exactas en la estación.
La pantalla SATQ mantiene los valores simulados.

## Archivos

- `openmeteo_huaycoloro_demo_20230312_18.json` y `openmeteo_huaycoloro_roj_20230312_18.json`: respuestas originales archivadas, 168 horas por punto.
- `lecturas_openmeteo_huaycoloro_demo_20230312_18.csv` y `lecturas_openmeteo_huaycoloro_roj_20230312_18.csv`: series normalizadas al esquema de `satq.validacion.cargar_lecturas_csv`. Cada registro conserva el offset `-05:00`, unidad, fuente y URL.
- `observaciones_senamhi_matucana_20230312_18.csv`: extracto de 168 observaciones horarias del CSV GBON/RBON público, preservando fecha y hora originales porque la ficha no declara la zona horaria.
- `diagnostico_proxy_senamhi_matucana_pod_far_csi_20230312_18.csv`: H/M/F, POD/FAR/CSI para 20, 30 y 40 mm/6 h usando MATUCANA como proxy regional; no equivale a desempeño local del SATQ.
- `eventos_huaycoloro2_20230312_18.csv`: cinco registros IGP con hora local y referencia PDF; marca el evento de las 15:28 del 15/03 para curación de episodio.
- `episodios_candidatos_huaycoloro2_20230312_18.csv`: vista derivada de cuatro episodios candidatos; integra dos registros separados por 44 min 19 s si se toma el 15/03 del campo interno del PDF discordante. La regla de brecha menor de 6 h es provisional y no sustituye la curación hidrológica del IGP.
- `chirps_climateserv_demo_20230312_18.json` y `chirps_climateserv_roj_20230312_18.json`: respuestas originales del API ClimateSERV, siete valores diarios de Global CHIRPS por punto.
- `chirps_climateserv_comparacion_diaria_20230312_18.csv`: 14 filas diarias normalizadas con etiqueta UTC, valor mm, operación, ID de extracción y referencia al resultado API. No tiene esquema horario y no debe cargarse como lluvia de pluviómetro en `cargar_lecturas_csv`.
- `imerg_v07late_demo_20230312_18.json` y `imerg_v07late_roj_20230312_18.json`: respuestas originales de NASA IMERG V07 Late 1 Day vía ClimateSERV (datatype 226), siete valores diarios por punto.
- `imerg_v07late_comparacion_diaria_20230312_18.csv`: 14 valores diarios IMERG con punto, fecha etiquetada UTC, mm, operación, ID de consulta y URL de extracción. No equivale a mm/6 h y no se carga en el lector de series horarias.
- `comparacion_umbral_huaycoloro2_20230312_18.csv`: sumas de las seis horas completas previas a cada registro en ambos puntos y nivel correspondiente a los umbrales demo.
- Los archivos `_20230312_15` son el primer corte de cuatro días y se conservan como muestra inicial.
- `openmeteo_huaycoloro_20230312.json`, `lecturas_openmeteo_huaycoloro_20230312.csv` y `eventos_huaycoloro_20230312.csv`: archivos del primer piloto de 24 horas, conservados como muestra inicial.

## Fuente horaria pública candidata: SENAMHI WIS 2.0

El catálogo público WIS 2.0 de SENAMHI declara observaciones sinópticas horarias
con variable precipitación ([colecciones](https://wis.senamhi.gob.pe/oapi/collections?f=html),
[ficha SYNOP horaria](https://wis.senamhi.gob.pe/oapi/collections/urn%3Awmo%3Amd%3Ape-senamhi%3Asynop-hourly?f=html)).
El inventario público contiene 31 estaciones e incluye ÑAÑA (`0-604-1-15474502`,
aprox. 12 km del punto demo), pero una consulta de solo lectura a la colección
SYNOP horaria para `2023-03-12/2023-03-19` devolvió cero observaciones para
ÑAÑA. La colección consultada sí devuelve reportes recientes de esa estación,
pero no el periodo histórico requerido. No se encontraron observaciones
horarias públicas de CHOSICA `151209` para marzo de 2023; WIS no se usó en las
métricas. El resultado de esta comprobación se registró en
`auditoria_fuente_senamhi_open_data_20261107.csv`.

Para el caso histórico se auditó el [Zarr público Source Cooperative de NASA GPM
IMERG Final](https://source.coop/bkr/imerg/gpm_final.zarr). El catálogo advierte
que el conjunto podría estar incompleto. NASA describe IMERG como una estimación
satelital en grilla de 0.1° con campos cada 30 minutos ([producto
IMERG](https://gpm.nasa.gov/data/imerg)). La metadata declara precipitación
`float32`, forma `[455809, 1800, 3600]` y chunks `[1, 1800, 3600]` (25,920,000
bytes por bloque temporal global sin comprimir). El eje temporal sí incluye el
caso: el índice `406618` es `2023-03-12 05:00 UTC`; la celda más cercana a los
puntos comparados es `-11.95, -76.95`. No obstante, el chunk de precipitación
`precipitation/c/406618/0/0` devuelve HTTP 404 en los espejos Early y Final; un
chunk antiguo sí existe. También se revisó el [repositorio Icechunk
Final](https://source.coop/bkr/imerg/imerg_final.icechunk): su eje temporal tiene
386016 registros, marcas fuera de orden y huecos no uniformes, y termina el
2020-07-12. Ninguna variante proporciona datos fiables para marzo de 2023, por
lo que IMERG no se incorporó a los cálculos POD/FAR/CSI. La auditoría está en
`auditoria_fuente_senamhi_open_data_20261107.csv`.

## Resultado del contraste

| Evento IGP (hora PET) | Punto demo | Referencia IGP/Jicamarca |
| --- | ---: | ---: |
| 12/03 17:43 | 0.1 mm/6 h | 0.0 mm/6 h |
| 14/03 15:24 | 4.9 mm/6 h | 5.5 mm/6 h |
| 15/03 14:44 | 0.9 mm/6 h | 0.0 mm/6 h |
| 15/03 15:28* | 0.7 mm/6 h | 0.3 mm/6 h |
| 18/03 17:54 | 0.5 mm/6 h | 0.4 mm/6 h |

Todos quedan bajo el umbral demostrativo moderado de 20 mm/6 h. Las activaciones
y horas son del IGP; Open-Meteo aporta precipitación estimada por modelo, no
observación de lluvia. El primer caso no reproduce la lluvia intensa que
SENAMHI reportó entre las 16:00 y 17:00 del 12/03. Este conjunto evidencia una
discrepancia del producto/punto, no un desempeño medido del SATQ. *El reporte
de 15:28 tiene portada del 17/03 y fecha interna del 15/03. La vista agrupada
es provisional y depende de que la fecha interna sea correcta. El protocolo
actual también evalúa ambas fechas sin agrupar.

## Contexto diario CHIRPS (no valida la ventana de 6 h)

Se consultó Global CHIRPS (ClimateSERV datatype 0, intervalo diario) del 12 al
18/03/2023 en los dos puntos documentados arriba. El 12/03 la API devolvió
1.0143 mm para el punto demo y 1.7002 mm para la referencia Jicamarca. Del 16
al 18/03 devolvió 0 mm en ambos puntos. Los valores exactos, los siete días y
los identificadores de trabajo están en el CSV; las respuestas originales se
conservan en JSON.

Esta fuente es una estimación areal, no una medición identificada de la estación
del puente. La respuesta de ClimateSERV no declara la versión CHIRPS ni la
ventana local del día; por eso estos valores quedan como contexto diario, no se
convierten a mm/6 h ni se comparan con el umbral operativo SATQ. Además, la
serie demo repite exactamente 1.0143002 mm del 12 al 15/03;
una consulta de un solo día para el 15/03 reprodujo 1.0143002 mm, confirmando
consistencia del API entre consulta puntual y rango, aunque esa repetición
requiere verificación independiente antes de interpretar patrones diarios.

La API documenta Global CHIRPS como datatype diario y permite obtener el
resultado por identificador de consulta ([API ClimateSERV](https://climateserv.readthedocs.io/en/latest/api.html)).
La [guía CHIRPS v3](https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/readme.txt)
se cita como contexto de esa versión, pero la respuesta del API aquí usada no
identifica su versión.

## Contexto diario IMERG V07 Late

Se consultó ClimateSERV datatype 226 (`NASA-IMERG-V07-Late 1 Day`) para las
mismas fechas y puntos. El 14/03 el punto demo arroja 24.7 mm y la referencia
Jicamarca 35.0 mm; el 15/03 los valores son 28.8 mm y 25.3 mm. El 12/03 son
0.9 mm y 4.2 mm, respectivamente. No interpretar estos acumulados diarios como
mediciones en la hora de activación: describen celdas satelitales, y los límites
de fecha diaria no coinciden necesariamente con ventanas locales de 6 h.

IMERG muestra lluvia diaria importante en los días 14–15 que el reanálisis
ECMWF IFS anterior no representa con sus seis horas previas a las activaciones.
Esta diferencia entre productos es evidencia de sensibilidad temporal/espacial
y una razón para no validar el umbral con una sola fuente. No significa por sí
sola que el motor SATQ haya fallado ni que los acumulados diarios superen el
umbral de 6 h. NASA describe IMERG como estimación combinada de múltiples
satélites, con productos de 30 minutos y diarios ([NASA GPM IMERG](https://gpm.nasa.gov/data/imerg)).

Para facilitar la siguiente evaluación, se generó una vista candidata de cuatro
episodios agrupando registros de la misma quebrada con una brecha menor de 6 h.
Así, las activaciones del 15/03 quedan como un solo episodio iniciado a las
14:44. Es una regla de curación provisional alineada con la ventana de lluvia
analizada, no una definición oficial del IGP; el CSV original de cinco reportes
se conserva intacto.

## Observaciones SENAMHI: acceso y licencia

En la verificación directa del portal oficial el 07/11/2026, el mapa y las
previsualizaciones de estación fueron accesibles sin iniciar sesión. CHOSICA
aparece con código `151209` en Lurigancho, Lima. HUARANGAL aparece con código
`000618` en Ancón y no se usa como sustituta geográfica para Huaycoloro. La
pestaña **Descarga** abrió `descarga/?p=login` y presentó un CAPTCHA; no se
introdujeron credenciales ni se intentó resolverlo. El CSV
`auditoria_estaciones_senamhi_20261107.csv` registra las estaciones, URLs y
resultado de acceso. La previsualización gráfica no proporciona por sí sola
una tabla horaria fechada ni datos de calidad para un backtest.

El repositorio describe otro conjunto SENAMHI como mediciones horarias validadas
de precipitación con metadatos de estación y lo cataloga como acceso abierto
([ficha ALICIA/CONCYTEC](https://alicia.concytec.gob.pe/vufind/Record/SEAM_28032c740124bd04c8f2a7b4e5f205f0/Details)).
Al inspeccionar el enlace del CSV el 2026-11-07, el servidor devolvió una página
de verificación antirobot y no el archivo. Además, el `license.txt` del recurso
es una plantilla de licencia de muestra, sin condiciones claras de reutilización.
Por eso no se incorporaron observaciones de ese archivo ni se intentó evadir el
control de acceso. La página de datos del mapa SENAMHI permite consultar la
ficha gráfica, mientras que el enlace de descarga estructurada conduce a la
pantalla de ingreso. La ficha abierta no prueba que el CSV sea libre de descargar
ni que su licencia permita redistribución.

### Catálogo nacional de datos abiertos

La [Plataforma Nacional de Datos Abiertos](https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-0)
publica un recurso SENAMHI GBON/RBON que, según su descripción, contiene
precipitación horaria validada y metadatos de estación. El catálogo indica un
CSV de 48,14 MB, con fecha de recurso 05/07/2024. El enlace directo no se pudo
previsualizar en Chrome (`ERR_BLOCKED_BY_CLIENT`), pero la descarga pública
posterior por la API del catálogo sí se completó. El archivo completo, hash,
licencia declarada, ausencia de CHOSICA `151209` y extracto de MATUCANA se
documentan más abajo y en `auditoria_fuente_senamhi_open_data_20261107.csv`.

### Serie diaria observada de CHOSICA

La [consulta pública de estaciones de SENAMHI](https://www.senamhi.gob.pe/?p=estaciones&dp=lima)
permite abrir la estación meteorológica convencional CHOSICA, código `151209`,
en Lurigancho. La tabla muestra la variable `Precipitación (mm/día)` y permite
consultar por mes; se extrajeron los 31 registros publicados para marzo de 2023
al seleccionar 2023-03. El portal atribuye los datos a SENAMHI/DRD y advierte:
“Datos sin control de calidad”. Los datos y sus referencias se guardan en
`observaciones_diarias_senamhi_chosica_151209_202303.csv`. El archivo que
compartiste, `111060_202303.csv`, confirma que `111060` es el identificador de
la selección del mapa: su encabezado identifica la estación como CHOSICA,
código SENAMHI `151209`, periodo 2023-03. Se archivó sin modificar como
`fuente_original_senamhi_111060_202303.csv`; sus 31 fechas y precipitaciones
coinciden con el CSV normalizado.

| Fecha | Precipitación diaria |
| --- | ---: |
| 2023-03-12 | 11.9 mm/día |
| 2023-03-14 | 14.9 mm/día |
| 2023-03-15 | 10.2 mm/día |
| 2023-03-18 | 9.5 mm/día |

En el archivo hay 31/31 fechas y valores numéricos, con máximo mensual de
14.9 mm/día. SHA-256 del CSV normalizado: `7EF322ADBC0A039502E089D64A30781A652FB45CC2A869E7C3744470F3BA1144`.
SHA-256 del CSV original compartido: `0AE270BC7D12A067F1AEB4C09F1E7032753FD48444890151F92B010EE76D4857`.
La tabla es una fuente observada diaria pero sin control de calidad; el valor
publicado por día no identifica cuándo cayó la lluvia durante esas 24 horas.
No se convirtió a mm/6 h ni se introdujo en el análisis de umbrales SATQ.

#### Uso permitido en la demostración y secuencia de validación

La ficha oficial `R4_SATQITO.pdf` define el prototipo actual como una
demostración con datos sintéticos, sin consumo de datos reales de SENAMHI/IGP.
Por coherencia con esa declaración, el registro diario observado de CHOSICA
`151209` y los reportes IGP de Huaycoloro 2 se presentan como **contexto y
motivación del caso**, no como validación del motor SATQ ni como cruce que
demuestre asociación lluvia-evento. La estación CHOSICA no tiene aquí
representatividad acreditada para el área aportante; la lluvia solo está
resuelta por día, carece de control de calidad en el portal y la fecha de un
reporte IGP sigue discordante (15/17). No se le aplican umbrales de seis horas
ni se calculan H/M/F, POD, FAR o CSI.

Para la demo de hoy, demostrar con el conjunto sintético reproducible las
capacidades que sí declara la ficha: ingesta y validación de datos, reglas
configurables sobre lluvia horaria y acumulado móvil de seis horas, estado
`DATOS_NO_DISPONIBLES` ante cobertura no verificable, trazabilidad de cambios
y avisos, y flujo de mensajería en modo simulado. Informar las pruebas
funcionales ya documentadas en la ficha como evidencia de funcionamiento del
prototipo, no de eficacia hidrológica ni de impacto comunitario. Mantener la
advertencia visible: SATQ Digital es un prototipo demostrativo, no es una
alerta oficial ni debe usarse para decisiones de emergencia.

La transición propuesta a piloto sigue las etapas del plan oficial: (1)
obtener y catalogar lluvia subdiaria observada representativa de la cuenca,
con cobertura, zona, semántica horaria, calidad y licencia; (2) obtener de IGP
la bitácora de detecciones y disponibilidad para resolver 15/17 e identificar
periodos sin evento; (3) sincronizar y curar ambas series, y evaluar reglas
configurables con el protocolo fijado (primer cruce de 20/30/40 mm en 6 h,
emparejamiento 1:1 dentro de 360 min, H/M/F y POD/FAR/CSI); (4) revisar los
umbrales con especialistas IGP/CENDEHUA y SENAMHI antes de cualquier
interpretación operativa; (5) acordar con la Municipalidad de Santa María de
Huachipa el protocolo de emisión, sectores destinatarios, acciones del aviso,
consentimiento y registro; (6) realizar pruebas de comprensión con residentes
y pruebas técnicas de latencia, disponibilidad y entrega; (7) ejecutar un
piloto controlado, con supervisión humana y coordinación con las alertas
oficiales, antes de considerar continuidad o ampliación. Un backtest de
alertas candidatas no sustituye el registro de alertas realmente emitidas para
medir desempeño operativo.

**Guion sugerido:** “SATQ Digital aborda el tramo final de comunicación: toma
datos, aplica reglas configurables y deja un aviso trazable que puede dirigirse
a comunidad y autoridades como complemento de los canales oficiales. Hoy
demostramos ese flujo funcional con datos sintéticos reproducibles; los
antecedentes observados de Huaycoloro motivan el caso, pero no calibran los
umbrales. El piloto queda condicionado a conseguir lluvia subdiaria
representativa, resolver la bitácora del IGP, revisar reglas con especialistas
y validar el mensaje con la municipalidad y la comunidad. El prototipo no es
una alerta oficial y no sirve para decisiones de emergencia.”

## Serie horaria pública SENAMHI GBON/RBON: Matucana

Se descargó el CSV público de [Datos Abiertos del Estado, publicado por
SENAMHI](https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio).
La ficha declara mediciones horarias validadas de precipitación, temperatura y
humedad, licencia Open Data Commons Attribution, cobertura 2015–2024 y archivo
de 48.14 MB. El archivo descargado contiene 416,273 filas; el SHA-256 es
`3D3E8A0A75E070D0B8111FAF921BE17140C3A0F9DB2B4C25D72D99A15A950EAB`. La copia
El CSV completo (48.14 MB) se conserva localmente y no se incluye en este PR. Se mantiene la ficha de metadatos en [`fuentes/senamhi_gbon_rbon_metadata.docx`](fuentes/senamhi_gbon_rbon_metadata.docx), junto con el extracto utilizado para el análisis.

El conjunto no incluye la estación CHOSICA `151209`. En marzo de 2023 hay cinco
estaciones en el archivo; la más cercana al punto demo es MATUCANA (`-11.8391,
-76.3780`, 2,421 m), aproximadamente a 63 km en línea recta de Huaycoloro
(`-11.95, -76.95`). Se extrajeron los registros del 12–18/03 a
`observaciones_senamhi_matucana_20230312_18.csv`: 168 valores horarios, sin
faltantes, en 163 ventanas completas de seis horas. El máximo móvil fue
10.7 mm/6 h. La metadata no especifica la zona horaria del campo `HORA`.

### Diagnóstico con la estación proxy

Se aplicaron las tres alertas candidatas por umbral que usa el motor de demo
(20, 30 y 40 mm/6 h) al registro horario de Matucana. No hubo cruces para
ningún umbral. Frente a los cuatro episodios IGP candidatos, los conteos son
H=0, M=4, F=0; por tanto POD=0.00, FAR indefinido (H+F=0) y CSI=0.00. El
resultado queda en `diagnostico_proxy_senamhi_matucana_pod_far_csi_20230312_18.csv`.

Es un **diagnóstico regional con estación proxy**, no una métrica de lluvia
observada en Huaycoloro ni de desempeño operativo del SATQ: Matucana está lejos
del punto de interés y no se pudo certificar que represente su microcuenca. La
zona horaria no declarada añade incertidumbre a la asociación temporal; dado
que no se produjo ninguna alerta candidata, el resultado del umbral en esta
semana no cambia con un desplazamiento horario. No se debe presentar como
validación local.

## Insumos faltantes para POD/FAR/CSI

La pantalla y el repositorio actual contienen escenario demostrativo, no una
bitácora de alertas SATQ emitidas entre el 12 y el 18/03/2023. La observación
diaria de CHOSICA no resuelve ventanas de seis horas. El CSV horario GBON/RBON
sí permite calcular un diagnóstico, pero MATUCANA, la estación más cercana
en ese archivo para el periodo, está aproximadamente a 63 km. Ni MATUCANA ni
la serie de Ñaña del visor acreditan representatividad para el área aportante
de Huaycoloro 2. Todavía no se calcula una métrica local del SATQ.

### Seguimiento de búsqueda pública en Chrome — 07/11/2026

Se continuó la búsqueda de los dos insumos faltantes sin repetir la extracción
de Ñaña, Matucana, reanálisis o acumulados diarios ya documentados. La búsqueda
se limitó a resultados públicos gratuitos, sin autenticación ni CAPTCHA. No se
encontró una serie observada horaria/subhoraria que pueda demostrarse
representativa del área aportante aguas arriba de Huaycoloro 2 para el
12–18/03/2023 con margen temporal, ni una bitácora pública IGP de detecciones
y disponibilidad que resuelva el registro fechado 15/03 en el campo interno y
17/03 en la portada.

Hallazgos útiles para gestionar los faltantes:

- La búsqueda pública localizó publicaciones de activación de CENDEHUA/IGP y
  el portal de [monitoreo y alerta en tiempo real](https://www.gob.pe/41855-centro-de-monitoreo-de-deslizamientos-y-huaicos), pero no un archivo de disponibilidad histórica ni una exportación de detecciones completa para la semana. Las publicaciones sociales no prueban continuidad del flujo ni disponibilidad del sensor.
- La página SENAMHI que compartiste, [Acceder al monitoreo meteorológico](https://www.gob.pe/institucion/senamhi/pages/93223-acceder-al-monitoreo-meteorologico), enlaza al [mapa de monitoreo de precipitación](https://www.senamhi.gob.pe/?&p=monitoreo-meteorologico). El mapa ofrece precipitación interpolada, caracterización diaria y acumulado de 7 días; su tabla descargable corresponde al mapa/fecha seleccionados y el listado visible cubría solo 15 fechas recientes (23/10–06/11/2026 al consultarlo). No ofrece el registro bruto horario/subhorario ni llega a marzo de 2023. No se descargó esa tabla porque no aporta el periodo ni la resolución requeridos.
- La misma página anuncia mapas nacionales interpolados, acumulados diarios y caracterización, no una serie de estación. Su acceso a [monitoreo del Observatorio Nacional del Tiempo, Agua y Clima](https://observatorio.senamhi.gob.pe/) también se revisó; la búsqueda interna de páginas por “Huaycoloro” no halló resultados. Esto no demuestra que no haya una estación o archivo interno. El resultado oficial de SENAMHI para [consultar datos de lluvia acumulada](https://www.gob.pe/9314-consultar-los-datos-de-lluvia-acumulada-a-nivel-nacional) describe datos diarios; no sirve para el protocolo de ventanas horarias. El portal de descarga ya auditado en este expediente requiere acceso/CAPTCHA. No se descargó ni incorporó otra serie.
- Se revisó además el [Catálogo de Metadatos IDESEP](https://idesep.senamhi.gob.pe/geonetwork/srv/spa/catalog.search#/search?any=Precipitaci%C3%B3n) que compartiste. La búsqueda “Precipitación” devolvió 58 fichas; el filtro de año de creación 2023 dejó 14, principalmente productos cartográficos/climáticos. Entre los resultados están mapas de anomalías del Niño Costero 2023, descritos como acumulados trimestrales (ENE–FEB–MAR y FEB–MAR–ABR), además de mapas mensuales/estacionales climatológicos. Sirven para contexto regional o para ubicar un contacto custodio; no identifican una estación y no tienen la resolución temporal necesaria para cruces de seis horas. La búsqueda directa “Huaycoloro” no devolvió fichas. No se interpretó el año de creación de metadatos como periodo observado.
- El [procedimiento general de acceso a información pública](https://www.gob.pe/20399-solicitar-acceso-a-la-informacion-publica) informa un plazo ordinario de hasta 10 días hábiles. El [trámite IGP de Mesa de Partes](https://www.gob.pe/20416-acceder-a-mesa-de-partes?child=27665) indica que el envío virtual requiere crear una cuenta; no se inició sesión. Consultas al IGP: `mesadepartes@igp.gob.pe`. Para datos meteorológicos, dirigir una solicitud equivalente a SENAMHI por su canal institucional de acceso a información.
- Se dejó [`solicitud_insumos_huaycoloro2_borrador.md`](solicitud_insumos_huaycoloro2_borrador.md) como borrador local no enviado, con especificación de los archivos y metadatos requeridos.

La consulta confirma la brecha documental, no la inexistencia de los registros en los archivos internos de las instituciones. Hasta recibirlos, no se procesan nuevos CSV ni se informan H/M/F, POD, FAR o CSI de lluvia local. Cualquier eventual reproducción con alertas calculadas a partir de umbrales será un **backtest de alertas candidatas**; para una evaluación operativa se necesitaría además el registro real de alertas SATQ emitidas, que el prototipo no conserva para marzo de 2023. El SATQ sigue siendo una demostración con datos/alertas simulados y no sirve para decisiones de emergencia.

### Corrida exploratoria con el reanálisis Open-Meteo

Para verificar el cálculo, se reprodujo el umbral demo moderado preexistente
(`20 mm/6 h`) sobre las dos series horarias ECMWF IFS del 12–18/03. Se tomaron
seis lecturas horarias consecutivas por ventana, se generó una alerta candidata
al primer cruce ascendente y se cotejó contra los cuatro episodios IGP
candidatos con una ventana de anticipación de 360 minutos.

| Serie | Lecturas | Ventanas completas | Máximo 6 h | H | M | F | POD | FAR | CSI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Punto demo SATQ | 168 | 163 | 7.4 mm | 0 | 4 | 0 | 0.00 | indefinido | 0.00 |
| Referencia IGP/Jicamarca | 168 | 163 | 5.5 mm | 0 | 4 | 0 | 0.00 | indefinido | 0.00 |

No se generaron alertas porque ambos máximos quedaron bajo 20 mm/6 h. Por
eso, `FAR = F / (H + F)` tiene denominador cero y se informa como indefinido.
El resumen está en
`diagnostico_exploratorio_openmeteo_pod_far_csi_20230312_18.csv`. Estos
valores son un diagnóstico del producto de reanálisis contra eventos IGP,
**no** un POD/FAR/CSI observacional ni el desempeño del SATQ en operación.

Para un **backtest por reproducción** no hace falta un log de alertas antiguas:
el motor genera las alertas candidatas al recorrer observaciones horarias con
umbrales y reglas fijados antes de analizar el periodo. Sigue faltando una
serie observada horaria representativa de Huaycoloro que cubra episodios y
periodos sin evento, con faltantes y calidad documentados. Un registro histórico
real de alertas sería necesario para evaluar el desempeño operativo tal como se
emitieron; no existe en el prototipo para marzo de 2023. El inventario IGP y el
diagnóstico exploratorio de reanálisis y proxy regional no sustituyen esos
insumos.

### Consulta horaria adicional: NASA POWER / MERRA-2

Se consultó [NASA POWER Hourly API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
para el punto SATQ (`-11.95, -76.95`) del 12 al 18/03/2023, en UTC. La respuesta
del parámetro `PRECTOT` identifica el campo devuelto como `PRECTOTCORR`, con
unidades mm/h y fuente MERRA-2. Se recibieron 168 marcas horarias; el máximo
horario mostrado fue 0.19 mm/h. Aun usando ese máximo repetido seis veces como
cota conservadora, cualquier acumulado de seis horas sería como máximo
1.14 mm/6 h, por debajo de los tres umbrales demo (20, 30 y 40 mm/6 h). Por
tanto, para cada umbral resultan H=0, M=4, F=0, POD=0.00, FAR indefinido y
CSI=0.00 frente a los cuatro episodios IGP candidatos. La tabla está en
`diagnostico_proxy_nasa_power_merra2_pod_far_csi_20230312_18.csv`.

Este resultado es un **contraste con reanálisis**, no una observación de
pluviómetro ni validación de Huaycoloro: NASA POWER entrega precipitación
MERRA-2 a resolución espacial nativa gruesa (aprox. 0.5° × 0.625°), de modo
que no representa la lluvia en la quebrada. Sirve para reproducir la
clasificación de umbrales y mostrar la sensibilidad a otra fuente, pero no
cambia la conclusión de que faltan observaciones horarias locales.

## Atribución y reproducción

Open-Meteo para uso no comercial requiere atribución y aplica licencia CC BY
4.0, sujeto a sus [términos de uso](https://open-meteo.com/en/terms). Consulta
la [documentación de datos históricos](https://open-meteo.com/en/docs/historical-weather-api).

La consulta NASA POWER/MERRA-2 se puede repetir con este enlace de API (respuesta
JSON, horas UTC):

```text
https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=PRECTOT&community=SB&longitude=-76.95&latitude=-11.95&start=20230312&end=20230318&format=JSON&time-standard=UTC
```

```powershell
$base = 'https://archive-api.open-meteo.com/v1/archive?start_date=2023-03-12&end_date=2023-03-18&hourly=precipitation&timezone=America%2FLima&models=ecmwf_ifs'
Invoke-RestMethod -Uri ($base + '&latitude=-11.95&longitude=-76.95')
Invoke-RestMethod -Uri ($base + '&latitude=-11.9523176&longitude=-76.8779755')
```

La extracción diaria ClimateSERV se realizó sin cuenta con `POST
https://climateserv.servirglobal.net/api/submitDataRequest/`: `datatype=0`
(Global CHIRPS) o `datatype=226` (NASA IMERG V07 Late 1 Day),
`begintime=03/12/2023`, `endtime=03/18/2023`, `intervaltype=0`,
`operationtype=5` (`avg`) y una geometría GeoJSON Point en EPSG:4326. Se
recuperaron los trabajos con `getDataRequestProgress/?id=...` y
`getDataFromRequest/?id=...`. Los UUID de cada respuesta están en los CSV y JSON.
El API devuelve fechas diarias; no aplicar el umbral de 6 h a estas series.

## SHA-256 del corte 12–18/03

Los hashes se calculan sobre el contenido exacto de cada archivo.

```text
E2690D21657F75F09DFB5655D1B6600F740DB601598D4EF19F9F153702A30667  openmeteo_huaycoloro_demo_20230312_18.json
7937B73E7CE4B3E49AA9648A9F6C7DB5FBFB43F9BF2046556E1B74C8792DC794  openmeteo_huaycoloro_roj_20230312_18.json
41AC81D334A862FFD5D4333804B399856CAC0E85BEBB2A428E37465E43ADE302  lecturas_openmeteo_huaycoloro_demo_20230312_18.csv
16C2D0BFEBED07DF9988C0A787E0F41659153DCD7DF40B5DBFB5F5334B77D773  lecturas_openmeteo_huaycoloro_roj_20230312_18.csv
87961FF644FD1E04C5900ADB615E9750024BAA78A24E52974B83A1AEC874DE7A  eventos_huaycoloro2_20230312_18.csv
BE2A5DFE7F02442AC13B9811C3B3D3283BCFFFFE4EDAF606CEB4870B85BF865D  comparacion_umbral_huaycoloro2_20230312_18.csv
8BB75EABB4F26DFB47FCA72B92E003D711A0D1E49FA6090CF4B0A5356EC8E90E  episodios_candidatos_huaycoloro2_20230312_18.csv
C1B260F8796BB017CB2D221455E8A4214F41B7C3D995CE76950D9CB9269DE782  chirps_climateserv_demo_20230312_18.json
15B716CD97E3C33A34337D48255DF31BC0ED8923AF3F2A9F020979885C6DCCBA  chirps_climateserv_roj_20230312_18.json
20413DAC352038BCCF0B1D7EA593F7EEF0B54A82606F20A5B2D299FC1F79301E  chirps_climateserv_comparacion_diaria_20230312_18.csv
9239D9E9595B7AAC9535347DCAF2D7F67B7776A384BB7473D4F28F2D3BAECFF8  imerg_v07late_demo_20230312_18.json
0619AD627297551319F62E69656BCFF16B75B134B2F191BF63D4C62D100D5CC2  imerg_v07late_roj_20230312_18.json
4D1399CB1F3BCE4CD288A720873177BDE8804B85C6D24BE40419F6EEDF6E1863  imerg_v07late_comparacion_diaria_20230312_18.csv
3AF95FD266163199BB56C9AA7CAC24489808ACEE54CF42A81F1841EE7B940C6A  observaciones_senamhi_matucana_20230312_18.csv
FBE16456C8BF20B43F4000F155549024890BED0C0C0B9FD3A4D30F87C91DEEB6  diagnostico_proxy_senamhi_matucana_pod_far_csi_20230312_18.csv
36E7D20A62226DABBB0609FC22D10CB7618768E0C03136EEE04C8403E366D987  diagnostico_proxy_nasa_power_merra2_pod_far_csi_20230312_18.csv
```

## Alternativas de evaluación en Lima

El [portal público del IGP para Lahares y Huaicos](https://grd.igp.gob.pe/lahares-huaicos/) confirma que su sistema monitorea en tiempo real, en Lurigancho-Chosica, **Huaycoloro 1, Huaycoloro 2, Río Seco 1 y Río Seco 2**. Esas dos quebradas Río Seco son candidatas para una futura comparación de cobertura de detecciones dentro de Lima. La página describe monitoreo de estado actual, pero no publica una bitácora histórica de 2023 ni disponibilidad pasada; cambiar a Río Seco, por sí solo, no resuelve la falta de lluvia horaria representativa.

**Recomendación:** no cambiar el caso histórico de Huaycoloro 2 para la demo actual. Mantener ese caso conserva los cinco reportes IGP ya curados y el expediente observacional existente, y presentar el flujo del SATQ como demostración simulada, sin puntaje local. Si el equipo necesita un segundo sitio del IGP para una futura demostración, explorar Río Seco 1/2 solo después de confirmar que SENAMHI/IGP pueden entregar tanto lluvia subdiaria representativa como registros históricos de detección y disponibilidad. Arequipa y Canchaque aparecen también en el portal, pero son contextos geográficos e hidrológicos distintos y no son sustitutos cercanos a Lima. No se recalcularon métricas ni se presentan proxies como validación local.
