# Validación y evidencia del SATQ Digital

## Alcance actual

La auditoría del 07/11/2026 recuperó [lluvia horaria observada de Ñaña automática, SENAMHI 111290](https://www.senamhi.gob.pe/mapas/mapa-estaciones-ms/map_red_graf.php?cod=111290), mediante el visor público. La estación está a 5,5 km de la referencia de Jicamarca, pero se ubica en el valle bajo del Rímac y no se justificó que represente la lluvia aguas arriba de Huaycoloro 2. Por ello **no hay POD, FAR o CSI de validación local**. El [protocolo reproducible](protocolo_huaycoloro2_202303.md) documenta el contraste con este proxy observado, tres lecturas posibles del inventario y cuatro supuestos de hora. En la semana, el máximo válido fue 9,2 mm/6 h. Para 20, 30 y 40 mm/6 h, con cuatro episodios candidatos: H=0, M=4, F=0, POD=0, FAR indefinido y CSI=0. Estos son resultados de Ñaña contra el inventario provisional, sin valor operativo.

El prototipo usa datos simulados y no debe emplearse para decisiones de emergencia. El módulo `satq.validacion` aporta piezas para evaluar episodios de alerta contra eventos documentados y cargar archivos normalizados con procedencia. Se descargó una muestra horaria gratuita de Open-Meteo para el evento de Huaycoloro del 12 de marzo de 2023. Es una estimación de reanálisis/modelo y no una observación de pluviómetro; por tanto, permite una comparación exploratoria, pero no constituye una validación operativa del SATQ.

## Método de evaluación por eventos

Una alerta cuenta como acierto si corresponde a la misma quebrada que un evento documentado y comienza entre 0 y 360 minutos antes de él. Cada alerta y cada evento se emparejan como máximo una vez. Los eventos se procesan cronológicamente y se asigna primero la alerta elegible más antigua, para preservar alertas recientes que también podrían corresponder a eventos posteriores. Con una ventana fija, esta regla maximiza el número de emparejamientos uno a uno. La ventana puede cambiarse al llamar `evaluar_eventos`, pero debe fijarse antes de analizar los resultados.

- **Acierto (H):** alerta emparejada con un evento.
- **Evento omitido (M):** evento sin alerta emparejada.
- **Falsa alarma (F):** alerta sin evento emparejado.
- **POD:** `H / (H + M)`.
- **FAR:** `F / (H + F)`.
- **CSI:** `H / (H + M + F)`.
- **Anticipación media:** promedio de minutos entre el inicio de cada alerta acertada y su evento documentado.

El resultado representa episodios, no horas de vigilancia. No hay verdaderos negativos ni se calcula especificidad porque el evaluador no recibe intervalos completos sin eventos. Si un denominador es cero, la proporción correspondiente se devuelve como `None`, no como cero.

## Archivos de entrada

`cargar_lecturas_csv` requiere estos encabezados exactos:

```csv
estacion,instante,precipitacion_mm,fuente,referencia
```

`cargar_eventos_csv` requiere:

```csv
quebrada,instante,fuente,referencia
```

`instante` debe tener formato ISO 8601 con zona horaria, por ejemplo `2023-03-12T17:44:00-05:00`. Los lectores lo convierten a UTC, rechazan instantes ambiguos, duplicados, cantidades negativas/no finitas y filas sin fuente o referencia. En lluvia, celda vacía, `NA`, `N/A` o `null` se preserva como `None`; jamás significa cero milímetros.

## Fuentes consultadas

1. **SENAMHI, Mapa de Descarga de Datos:** [página oficial](https://www.senamhi.gob.pe/site/descarga-datos/). La inspección directa del portal en Chrome el 07/11/2026 confirmó la ficha pública de CHOSICA (código `151209`, distrito de Lurigancho) y la ficha de HUARANGAL (código `000618`, distrito de Ancón). La previsualización pública ofrece un gráfico de precipitación y temperaturas, pero la pestaña de descarga abre el inicio de sesión con CAPTCHA. No se ingresaron credenciales ni se descargó un CSV. El inventario y las URLs observadas constan en `datos/validacion/auditoria_estaciones_senamhi_20261107.csv`.
2. **SENAMHI, consulta pública de estaciones:** [Datos Hidrometeorológicos en Lima](https://www.senamhi.gob.pe/?p=estaciones&dp=lima). En la tabla de CHOSICA `151209` se consultó marzo de 2023 y se transcribió la columna **Precipitación (mm/día)**. El usuario compartió `111060_202303.csv`; su encabezado confirma CHOSICA, código `151209`, periodo 2023-03, y sus 31 lecturas coinciden con la versión normalizada. El portal atribuye los datos a SENAMHI/DRD y advierte que no tienen control de calidad. El original archivado, la extracción normalizada y sus hashes están en `datos/validacion/` y `datos/validacion/README.md`. Es evidencia observada diaria, no una serie horaria.
3. **INDECI, Informe de Emergencia 637 — lluvias intensas en Lima:** [PDF oficial](https://portal.indeci.gob.pe/wp-content/uploads/2023/03/INFORME-DE-EMERGENCIA-N%C2%BA-637-21MAR2023-LLUVIAS-INTENSAS-EN-EL-DEPARTAMENTO-DE-LIMA-13-DEE.pdf). Incluye reportes de activación de quebradas, entre ellas Huaycoloro 1 y 2. Al construir el inventario se debe registrar página/tabla y distinguir la hora de reporte de la hora observada de inicio del evento.
4. **CENEPRED, evaluación de riesgo por flujo de detritos en Huaycoloro:** [ficha SIGRID](https://sigrid.cenepred.gob.pe/sigridv3/documento/4121). Sirve como contexto de peligro y ubicación; no es una serie de eventos ni reemplaza mediciones pluviométricas.
5. **Open-Meteo Historical Weather API:** [documentación](https://open-meteo.com/en/docs/historical-weather-api) y [condiciones de uso](https://open-meteo.com/en/terms). La API pública permite consultas horarias sin cuenta para uso no comercial. Se conserva la atribución Open-Meteo y el modelo seleccionado. Su precipitación es salida de modelo/reanálisis, con escala espacial de kilómetros, no una medición puntual.
6. **IGP, reporte de activación Huaycoloro 2:** [PDF oficial](https://www.igp.gob.pe/servicios/centro-monitoreo-deslizamientos-huaicos/sites/default/files/reportes/Evento_12_03_2023_HL2.pdf). Registra el evento a las 17:43 hora local y lo ubica junto al puente de ingreso al Radio Observatorio de Jicamarca. Las coordenadas del observatorio se documentan en [IGP](https://www.gob.pe/institucion/igp/campa%C3%B1as/1256-ministra-del-ambiente-visitara-el-radar-mas-grande-y-potente-del-mundo-por-98-aniversario-del-igp).
7. **SENAMHI, reporte público del evento:** [noticia oficial](https://www.gob.pe/institucion/senamhi/noticias/724402-quebrada-huaycoloro-se-activa-por-intensas-lluvias). Señala lluvia en las cuencas media y alta del Rímac desde las 14:00, con mayor intensidad entre 16:00 y 17:00 del 12 de marzo de 2023.
8. **SENAMHI, conjunto GBON/RBON registrado en ALICIA:** [ficha del repositorio ALICIA](https://alicia.concytec.gob.pe/vufind/Record/SEAM_28032c740124bd04c8f2a7b4e5f205f0/Details). La ficha secundaria describe observaciones horarias validadas, pero el enlace directo a su copia no se usó porque respondió con una verificación antirobot y su archivo `license.txt` no aclara los términos. Para evitar depender de esa copia, la descarga y licencia se verificaron en la Plataforma Nacional de Datos Abiertos, documentada en el punto siguiente.
9. **SENAMHI, variables meteorológicas GBON/RBON en Datos Abiertos:** [ficha pública](https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-0). La ficha declara mediciones horarias validadas de precipitación, temperatura y humedad, licencia Open Data Commons Attribution, cobertura 2015–2024 y archivo de 48.14 MB. La descarga pública se verificó por la API del catálogo; el archivo tiene 416,273 filas y SHA-256 `3D3E8A0A75E070D0B8111FAF921BE17140C3A0F9DB2B4C25D72D99A15A950EAB`. No contiene CHOSICA `151209`; para marzo de 2023 la estación más cercana del archivo es MATUCANA, a unos 63 km, y su zona horaria no está especificada. Se usa únicamente para un diagnóstico proxy regional, no para validar localmente el SATQ. El detalle y extracto están en `datos/validacion/` y `auditoria_fuente_senamhi_open_data_20261107.csv`.
10. **ClimateSERV / CHIRPS:** [API oficial](https://climateserv.readthedocs.io/en/latest/api.html) identifica Global CHIRPS como conjunto diario y documenta consultas por geometría. La respuesta no declara la versión ni la ventana local del día, así que se conserva solo como contexto areal, no como pluviómetro ni como medición horaria. La [documentación diaria de CHIRPS v3](https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/readme.txt) se cita como contexto de esa versión y no se atribuye directamente a esta extracción.
11. **NASA IMERG vía ClimateSERV:** la [API ClimateSERV](https://climateserv.readthedocs.io/en/latest/api.html) lista datatype 226 como NASA IMERG V07 Late 1 Day; NASA explica que IMERG ofrece estimaciones de precipitación combinadas de satélites en productos subdiarios y diarios ([GPM IMERG](https://gpm.nasa.gov/data/imerg)). Aquí solo se descargó el producto diario.
12. **SENAMHI WIS 2.0, observaciones sinópticas horarias:** el [catálogo de colecciones](https://wis.senamhi.gob.pe/oapi/collections?f=html) publica una colección horaria. Su inventario contiene 31 estaciones, incluida ÑAÑA (`0-604-1-15474502`), a unos 12 km del punto demo. La consulta de observaciones por estación y por fechas `2023-03-12/2023-03-19` devolvió cero registros; tampoco hay cobertura del periodo en CHOSICA `151209`. La colección tiene reportes recientes, pero no ofrece la serie histórica requerida para este backtest. Se registra como vía verificada y no utilizable para marzo de 2023 en `datos/validacion/auditoria_fuente_senamhi_open_data_20261107.csv`.
13. **NASA GPM IMERG media hora, espejo público Source Cooperative:** el [producto oficial IMERG](https://gpm.nasa.gov/data/imerg) ofrece estimaciones satelitales cada 30 minutos; el [Zarr público GPM Final](https://source.coop/bkr/imerg/gpm_final.zarr) se describe desde 2000 y advierte que el conjunto podría estar incompleto. La metadata declara precipitación `float32` de forma `[455809, 1800, 3600]` y chunks `[1, 1800, 3600]`; cada bloque temporal global ocupa 25,920,000 bytes sin comprimir. Se descargaron los ejes pequeños de coordenadas: el índice temporal `406618` corresponde a `2023-03-12 05:00 UTC`, y la celda de grilla más cercana a los dos puntos del contraste es `lat=-11.95`, `lon=-76.95` (`lat_index=780`, `lon_index=1030`). Sin embargo, el objeto de precipitación de ese instante (`precipitation/c/406618/0/0`) devuelve HTTP 404 tanto en `gpm_final.zarr` como en `gpm_early.zarr`; un chunk antiguo (`c/0/0/0`) sí existe. Por ello, el espejo Zarr cubre la fecha en el eje temporal, pero no proporciona el bloque de lluvia requerido. También se inspeccionó el [repositorio público Icechunk Final](https://source.coop/bkr/imerg/imerg_final.icechunk): su eje temporal tiene 386016 registros, incluye valores fuera de orden y huecos distintos de 30 minutos, y el último tiempo publicado es `2020-07-12 23:30 UTC`; no cubre marzo de 2023 ni sirve para esta evaluación. Ninguna de estas series es un pluviómetro; IMERG no se usó para calcular puntajes.

### Auditoría preliminar de la ficha CHOSICA

El mapa y la previsualización de CHOSICA son visibles sin iniciar sesión, pero el control **Descarga** conduce a `descarga/?p=login`, donde se muestra CAPTCHA. Por ello, no se confirmó que la descarga de observaciones esté disponible sin cuenta; tampoco se intentó resolver el CAPTCHA ni acceder con una cuenta ajena. La ficha identifica CHOSICA como Lurigancho, Lima (código `151209`). HUARANGAL aparece en el mismo mapa, pero la ficha la ubica en Ancón (código `000618`), de modo que no se considera sustituta espacial de CHOSICA para Huaycoloro.

Se descargó el CSV GBON/RBON horario y se comprobó su cobertura: el recurso no incluye CHOSICA `151209`. Para marzo de 2023 contiene datos horarios de MATUCANA, la estación más cercana hallada en ese mes, a unos 63 km de Huaycoloro. Se incorporó un extracto y un diagnóstico de umbral proxy al expediente; por la distancia y la zona horaria no especificada, el resultado no cuenta como validación local. Open-Meteo permanece como contraste exploratorio separado.

También se verificó el catálogo WIS 2.0 en modo lectura. Su inventario devuelve ÑAÑA como estación cercana, pero la API devuelve cero observaciones para esa estación durante el periodo de marzo de 2023. Los reportes WIS actuales no cubren el caso histórico y no se incorporaron al cálculo.

La comprobación directa del [Zarr público de IMERG](https://source.coop/bkr/imerg/gpm_final.zarr) confirmó que el eje temporal sí incluye marzo de 2023 y permitió ubicar la celda de grilla más cercana (`-11.95, -76.95`). Al pedir el chunk de precipitación correspondiente al primer instante del caso, Source Cooperative respondió HTTP 404 en las versiones Early y Final, aunque un chunk antiguo sí está publicado. El objeto temporal por sí solo no demuestra que exista el campo de lluvia. La alternativa [Icechunk Final](https://source.coop/bkr/imerg/imerg_final.icechunk) tampoco es utilizable para el caso: su serie temporal termina en julio de 2020 y contiene marcas fuera de orden y huecos irregulares. Se descarta esta vía como insumo del backtest; IMERG no se incorporó a los puntajes.

Por otra vía, la consulta pública de estaciones sí permitió recuperar lluvia **diaria observada** de CHOSICA `151209` para marzo de 2023. En las cuatro fechas de episodios candidatos (12, 14, 15 y 18/03) el portal muestra 11,9; 14,9; 10,2 y 9,5 mm/día, respectivamente. La serie indica que es una estación convencional meteorológica y advierte que los datos no tienen control de calidad. Es una mejora de evidencia observacional, pero los acumulados diarios no dan la distribución intradiaria ni permiten probar los umbrales del prototipo, expresados en mm/6 h. No se generaron alertas históricas a partir de estos totales.

La previsualización del mapa antiguo representa precipitación y categorías por año, pero no expone en el eje la fecha completa de cada punto. En la inspección del gráfico se observaron 8,828 categorías y 8,829 valores de precipitación; 450 valores están nulos. Esa vista gráfica no es la serie diaria recién extraída de la consulta pública de estaciones y tampoco sirve como serie alineada para backtest. La observación diaria consultada queda separada en [`observaciones_diarias_senamhi_chosica_151209_202303.csv`](../datos/validacion/observaciones_diarias_senamhi_chosica_151209_202303.csv); el detalle de acceso al mapa antiguo sigue en [`auditoria_estaciones_senamhi_20261107.csv`](../datos/validacion/auditoria_estaciones_senamhi_20261107.csv).

Además, la serie de la estación CHOSICA no debe tratarse automáticamente como lluvia representativa de la cuenca de Huaycoloro. La selección de estación o estaciones debe justificarse hidrológicamente.

### Curación provisional de episodios

`episodios_candidatos_huaycoloro2_20230312_18.csv` agrupa provisionalmente dos detecciones separadas por 44 min 19 s **si** la fecha interna del 15/03 es correcta. La portada del segundo reporte dice 17/03, lo que produciría un episodio separado. INDECI confirma actividad el 15/03, pero su hora de reporte no permite decidir entre las interpretaciones ni si hubo continuidad de flujo. Se mantienen los cinco registros y se muestran escenarios separados en la [revisión de cronología](protocolo_huaycoloro2_202303.md#revisión-de-las-detecciones).

## Contraste exploratorio: Huaycoloro 2, 12–18 de marzo de 2023

El [inventario inicial](../datos/validacion/eventos_huaycoloro2_20230312_18.csv) reúne cinco detecciones de Huaycoloro 2 en hora local. Los diagnósticos previos usaron el campo interno 15/03 para el reporte con portada 17/03 y agruparon las dos detecciones del día con una brecha menor a 6 h. El [protocolo](protocolo_huaycoloro2_202303.md) distingue la fecha de portada, la detección local y las horas administrativas, y conserva la alternativa sin agrupar.

Se descargó lluvia horaria del 12 al 18 de marzo (168 horas) en dos coordenadas: el punto de demostración SATQ (`-11.95, -76.95`) y la referencia del Radio Observatorio de Jicamarca (`-11.9523176, -76.8779755`). La segunda es una referencia geográfica pública próxima al puente descrito por el IGP, no la coordenada certificada de la estación. Open-Meteo devolvió celdas distintas: `-11.915641, -76.92377` (798 m) para el punto demo y `-11.98594, -76.91202` (496 m) para Jicamarca. La resolución nominal del modelo ECMWF IFS es de alrededor de 9 km, por lo que esta comparación mide sensibilidad a la grilla y no representa dos pluviómetros.

Para cada activación se sumaron las seis lecturas horarias completas inmediatamente anteriores a la hora del evento. Los datos y el cálculo reproducible están en `comparacion_umbral_huaycoloro2_20230312_18.csv`:

| Activación IGP (PET) | Punto demo SATQ | Referencia IGP/Jicamarca | Umbral moderado demo |
| --- | ---: | ---: | --- |
| 12/03 17:43 | 0.1 mm/6 h | 0.0 mm/6 h | No alcanzado (<20 mm) |
| 14/03 15:24 | 4.9 mm/6 h | 5.5 mm/6 h | No alcanzado (<20 mm) |
| 15/03 14:44 | 0.9 mm/6 h | 0.0 mm/6 h | No alcanzado (<20 mm) |
| 15/03 15:28* | 0.7 mm/6 h | 0.3 mm/6 h | No alcanzado (<20 mm) |
| 18/03 17:54 | 0.5 mm/6 h | 0.4 mm/6 h | No alcanzado (<20 mm) |

*La ventana de 15:28 se conserva en la comparación de registros, pero ambas activaciones pertenecen provisionalmente a un episodio cuyo inicio se fija a las 14:44 en el inventario derivado. El máximo móvil de seis horas en el periodo completo fue 7.4 mm en la grilla del punto demo y 5.5 mm en la grilla de Jicamarca. Todas las ventanas previas quedan bajo 20 mm/6 h, el umbral moderado de demostración. En particular, el primer evento no coincide temporalmente con el reporte de SENAMHI de lluvia intensa entre 16:00 y 17:00 el 12/03. Esta discrepancia advierte que Open-Meteo IFS, en esta grilla y periodo, no puede tratarse como una observación local de lluvia ni como verdad de terreno para validar los umbrales. No se atribuye al motor un fallo operativo: faltan mediciones pluviométricas representativas y una serie histórica de alertas reales.

La pantalla SATQ que muestra 42 mm/6 h al nivel Crítico pertenece al escenario simulado actual y no a este periodo histórico. Aún no hay POD/FAR/CSI observacionales locales ni desempeño real del SATQ: el piloto tiene cinco reportes IGP (uno agrupado en la vista provisional), pero no una serie de pluviómetro horaria representativa de Huaycoloro. Además del diagnóstico exploratorio de reanálisis Open-Meteo, se calculó un diagnóstico regional con datos horarios observados de la estación SENAMHI MATUCANA, a unos 63 km. Ninguno debe interpretarse como habilidad operativa del SATQ. Las respuestas, series, eventos, comparaciones y hashes están documentados en [`datos/validacion/README.md`](../datos/validacion/README.md).

### Diagnóstico exploratorio POD/FAR/CSI con Open-Meteo

Se recorrieron las 168 lecturas horarias por punto con 163 ventanas completas de
seis observaciones consecutivas. Se aplicó el umbral demo preexistente de
moderado (`20 mm/6 h`) y se definió una alerta candidata al primer cruce
ascendente; se comparó contra los cuatro episodios IGP candidatos usando la
ventana de emparejamiento de seis horas.

| Serie de precipitación | Máximo móvil | H | M | F | POD | FAR | CSI | Anticipación |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Open-Meteo ECMWF IFS, punto demo | 7.4 mm/6 h | 0 | 4 | 0 | 0.00 | indefinido | 0.00 | n/a |
| Open-Meteo ECMWF IFS, Jicamarca | 5.5 mm/6 h | 0 | 4 | 0 | 0.00 | indefinido | 0.00 | n/a |

FAR es indefinido, no cero: su denominador `H + F` es cero porque no hubo
alertas candidatas. El archivo reproducible está en
[`datos/validacion/diagnostico_exploratorio_openmeteo_pod_far_csi_20230312_18.csv`](../datos/validacion/diagnostico_exploratorio_openmeteo_pod_far_csi_20230312_18.csv).
Estos puntajes describen solo un reanálisis de precipitación comparado con
eventos IGP; no son métricas observacionales ni de operación del SATQ.

### Diagnóstico proxy regional con SENAMHI GBON/RBON

La ficha pública de [SENAMHI en Datos Abiertos](https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio)
declara observaciones horarias validadas de precipitación. El archivo descargado
no contiene CHOSICA `151209`; para marzo de 2023 la estación disponible más
cercana fue MATUCANA, a aproximadamente 63 km del punto demo. Sus 168 horas
válidas (12–18/03) contienen 163 ventanas completas; la máxima acumulación fue
10.7 mm/6 h. Se evaluaron los tres límites de demostración (20/30/40 mm/6 h):

| Umbral | H | M | F | POD | FAR | CSI | Resultado |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 20 mm/6 h | 0 | 4 | 0 | 0.00 | indefinido | 0.00 | Ningún cruce |
| 30 mm/6 h | 0 | 4 | 0 | 0.00 | indefinido | 0.00 | Ningún cruce |
| 40 mm/6 h | 0 | 4 | 0 | 0.00 | indefinido | 0.00 | Ningún cruce |

FAR queda indefinido porque no hubo alertas candidatas (`H+F=0`). Es un
diagnóstico de umbral con una **estación proxy distante**, no una validación
local de lluvia en Huaycoloro. La ficha no especifica la zona horaria de `HORA`;
la serie tampoco permite atribuir al SATQ un acierto o fallo operativo. Los
registros extraídos y la tabla reproducible están en `datos/validacion/`.

### Contraste adicional con NASA POWER / MERRA-2

La API horaria pública de [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
devolvió 168 horas de precipitación para el punto demo (`-11.95, -76.95`) entre
el 12 y el 18/03/2023. El producto identificado es MERRA-2; la respuesta usa
UTC y reporta `PRECTOTCORR` en mm/h. El mayor valor horario mostrado fue
0.19 mm/h, de modo que incluso la cota conservadora de seis horas
(`6 × 0.19 = 1.14 mm`) queda muy por debajo del umbral moderado de 20 mm/6 h.
No hubo alertas candidatas para los tres umbrales demo (20/30/40 mm/6 h): en
cada corte H=0, M=4, F=0, POD=0.00, FAR indefinido y CSI=0.00.

La cota usa los máximos horarios devueltos y evita afirmar un máximo móvil
exacto. NASA POWER identifica MERRA-2 y sirve aquí como una segunda serie de
reanálisis, con resolución espacial mucho más gruesa que la quebrada. Por eso
el resultado es otra **prueba de cálculo por proxy**, no una validación local
ni operativa. La consulta y los conteos se conservan en
[`datos/validacion/diagnostico_proxy_nasa_power_merra2_pod_far_csi_20230312_18.csv`](../datos/validacion/diagnostico_proxy_nasa_power_merra2_pod_far_csi_20230312_18.csv).

## Contraste contextual diario con CHIRPS

El API ClimateSERV devolvió siete valores diarios de Global CHIRPS (datatype 0, versión no declarada en la respuesta) para cada punto consultado. Para el 12/03/2023 reportó 1.0143 mm en el punto demo SATQ y 1.7002 mm en la referencia Jicamarca; los resultados completos, referencias y respuestas originales se encuentran en `datos/validacion/chirps_climateserv_comparacion_diaria_20230312_18.csv` y los JSON asociados. Una consulta aislada del 15/03 en el punto demo reprodujo el valor que devolvió la consulta semanal.

La serie demo repite exactamente 1.0143002 mm del 12 al 15/03, un patrón que requiere contraste independiente. Además, la fecha diaria CHIRPS no asegura una ventana local uniforme y no permite reconstruir lluvia antecedente de seis horas. Por tanto, el resultado amplía la evidencia espacial diaria, pero no resuelve la falta de observación de pluviómetro representativa ni autoriza calcular POD/FAR/CSI.

## Contraste contextual diario con IMERG V07 Late

ClimateSERV datatype 226 (`NASA-IMERG-V07-Late 1 Day`) devolvió siete valores diarios en cada punto. Para el 12/03 reportó 0.9 mm en el punto demo y 4.2 mm en Jicamarca. Para el 14/03, 24.7 mm y 35.0 mm; para el 15/03, 28.8 mm y 25.3 mm. Las series completas y sus respuestas originales están en `datos/validacion/imerg_v07late_comparacion_diaria_20230312_18.csv` y los JSON asociados.

Los acumulados diarios IMERG de 14–15/03 contrastan con las sumas Open-Meteo IFS de las seis horas anteriores a los reportes (4.9/5.5 mm el 14/03 y 0.9/0.0 mm el 15/03 en demo/Jicamarca). Las ventanas de acumulación son distintas, así que no constituyen una comparación equivalente ni una prueba de que se superara el umbral de 6 h. La discrepancia entre fuentes justifica conservar ambos productos, revisar cobertura espacial/fecha y buscar una medición de estación antes de emitir juicios de rendimiento.

Como control descriptivo, se listan los acumulados del día UTC que contiene cada inicio de episodio candidato. Estos totales incluyen horas posteriores al evento y no representan lluvia antecedente:

| Fecha UTC del inicio | CHIRPS demo / Jicamarca (mm/día) | IMERG V07 Late demo / Jicamarca (mm/día) |
| --- | ---: | ---: |
| 12/03 | 1.0143 / 1.7002 | 0.9 / 4.2 |
| 14/03 | 1.0143 / 1.7002 | 24.7 / 35.0 |
| 15/03 | 1.0143 / 3.4004 | 28.8 / 25.3 |
| 18/03 | 0.0 / 0.0 | 0.0 / 0.6 |

## Evidencia mínima para un backtest defendible

1. Conservar el archivo original de SENAMHI sin editar; registrar fecha de descarga, URL, estación/código, frecuencia, periodo, unidad y hash SHA-256.
2. Normalizar una copia a `lecturas.csv`, conservando vacíos y control de calidad; registrar filas leídas, faltantes, duplicados y filas rechazadas.
3. Curar `eventos.csv` desde reportes oficiales. Cada fila debe tener quebrada, instante con zona horaria, fuente y referencia precisa a página/tabla. Dejar constancia de la definición de evento y de cualquier ambigüedad temporal.
4. Confirmar que la frecuencia permite calcular la ventana del motor. Los umbrales actuales están expresados en mm/6 h; datos diarios no permiten validar directamente esos umbrales.
5. Definir umbrales y anticipación antes del periodo de evaluación. Si se ajustan, separar periodos de calibración y evaluación para no medir en los mismos eventos usados para elegir los límites.
6. Reportar conteos H/M/F, POD, FAR, CSI, anticipación, periodo evaluado, cobertura y faltantes, lista auditable de emparejamientos y supuestos. No presentar métricas unitarias con datos sintéticos como desempeño real.

## Estado de la evidencia

Las pruebas del módulo usan ejemplos sintéticos para verificar reglas y validaciones de formato. Se conservan cinco registros IGP y una vista provisional de cuatro episodios. El expediente reúne estimaciones de reanálisis, series diarias y dos contrastes horarios observados: MATUCANA (proxy regional) y Ñaña (proxy cercano). Para una reproducción local siguen faltando observaciones horarias representativas de Huaycoloro y un inventario de detecciones y de cobertura IGP que permita distinguir periodos sin evento de periodos sin información. Una bitácora real de alertas permitiría además evaluar el desempeño operativo de las alertas emitidas.
