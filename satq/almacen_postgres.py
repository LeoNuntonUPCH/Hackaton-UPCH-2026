from __future__ import annotations

import os
from pathlib import Path

from .datos import Alerta, CambioParametro, Comunicacion, Quebrada
from .motor import Umbrales

DSN = os.environ.get("SATQ_DSN", "postgresql://postgres@localhost:5432/satq")
RUTA_SQL = Path(__file__).parent / "migraciones" / "001_inicial.sql"


def habilitado() -> bool:
    return os.environ.get("SATQ_DB", "memory").lower() == "postgres"


def _conectar():
    import psycopg
    return psycopg.connect(DSN)


def crear_esquema() -> None:
    with _conectar() as cx, cx.cursor() as cur:
        cur.execute(RUTA_SQL.read_text(encoding="utf-8"))
    # psycopg hace commit al salir del bloque


def _vacio() -> bool:
    with _conectar() as cx, cx.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM quebradas")
        return cur.fetchone()[0] == 0


def cargar(estado) -> None:
    repo = estado.repo
    with _conectar() as cx, cx.cursor() as cur:
        cur.execute("SELECT codigo, nombre, distrito, provincia, departamento, "
                    "lat, lon, destinatarios, grupo, destacada, lecturas FROM quebradas")
        repo._quebradas = {
            r[0]: Quebrada(codigo=r[0], nombre=r[1], distrito=r[2], provincia=r[3],
                           departamento=r[4], lat=r[5], lon=r[6], destinatarios=r[7],
                           grupo=r[8], destacada=r[9], lecturas=list(r[10]))
            for r in cur.fetchall()
        }
        cur.execute("SELECT codigo, quebrada, momento, nivel, estado, fuente, "
                    "acumulado, nota FROM alertas")
        repo._alertas = [Alerta(codigo=r[0], quebrada=r[1], momento=r[2], nivel=r[3],
                                estado=r[4], fuente=r[5], acumulado=r[6], nota=r[7])
                         for r in cur.fetchall()]
        cur.execute("SELECT momento, quebrada, destinatarios, canal, resultado, "
                    "entrega_real FROM comunicaciones ORDER BY momento DESC")
        repo._comunicaciones = [Comunicacion(momento=r[0], quebrada=r[1],
                                             destinatarios=r[2], canal=r[3],
                                             resultado=r[4], entrega_real=r[5])
                                for r in cur.fetchall()]
        cur.execute("SELECT momento, parametro, responsable, critico "
                    "FROM historial_parametros ORDER BY momento DESC")
        repo._historial = [CambioParametro(momento=r[0], parametro=r[1],
                                           responsable=r[2], critico=r[3])
                           for r in cur.fetchall()]
        cur.execute("SELECT bajo, moderado, alto, critico, ventana_horas "
                    "FROM umbrales WHERE id = 1")
        fila = cur.fetchone()
        if fila:
            repo._umbrales = Umbrales(bajo=fila[0], moderado=fila[1], alto=fila[2],
                                      critico=fila[3], ventana_horas=fila[4])
        cur.execute("SELECT clave, huella, resultado FROM ingestas")
        repo._ingestas = {
            r[0]: (r[1], dict(r[2])) for r in cur.fetchall()
        }
        cur.execute("SELECT clave, huella, resultado FROM alertas_clave")
        repo._alertas_por_clave = {
            r[0]: (r[1], dict(r[2])) for r in cur.fetchall()
        }


def guardar(estado) -> None:
    from psycopg.types.json import Jsonb
    with _conectar() as cx, cx.cursor() as cur:
        cur.execute("TRUNCATE quebradas, alertas, comunicaciones, "
                    "historial_parametros, umbrales, ingestas, alertas_clave")
        for q in estado.quebradas.values():
            cur.execute(
                "INSERT INTO quebradas (codigo, nombre, distrito, provincia, "
                "departamento, lat, lon, destinatarios, grupo, destacada, lecturas) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (q.codigo, q.nombre, q.distrito, q.provincia, q.departamento,
                 q.lat, q.lon, q.destinatarios, q.grupo, q.destacada,
                 Jsonb(q.lecturas)),
            )
        for a in estado.alertas:
            cur.execute(
                "INSERT INTO alertas (codigo, quebrada, momento, nivel, estado, "
                "fuente, acumulado, nota) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (a.codigo, a.quebrada, a.momento, a.nivel, a.estado,
                 a.fuente, a.acumulado, a.nota),
            )
        for c in estado.comunicaciones:
            cur.execute(
                "INSERT INTO comunicaciones (momento, quebrada, destinatarios, "
                "canal, resultado, entrega_real) VALUES (%s,%s,%s,%s,%s,%s)",
                (c.momento, c.quebrada, c.destinatarios, c.canal,
                 c.resultado, c.entrega_real),
            )
        for h in estado.historial_parametros:
            cur.execute(
                "INSERT INTO historial_parametros (momento, parametro, responsable, "
                "critico) VALUES (%s,%s,%s,%s)",
                (h.momento, h.parametro, h.responsable, h.critico),
            )
        u = estado.umbrales
        cur.execute(
            "INSERT INTO umbrales (id, bajo, moderado, alto, critico, ventana_horas) "
            "VALUES (1,%s,%s,%s,%s,%s)",
            (u.bajo, u.moderado, u.alto, u.critico, u.ventana_horas),
        )
        repo = estado.repo
        for clave, (huella, resultado) in repo._ingestas.items():
            cur.execute(
                "INSERT INTO ingestas (clave, huella, resultado) "
                "VALUES (%s,%s,%s)",
                (clave, huella, Jsonb(resultado)),
            )
        for clave, (huella, resultado) in repo._alertas_por_clave.items():
            cur.execute(
                "INSERT INTO alertas_clave (clave, huella, resultado) "
                "VALUES (%s,%s,%s)",
                (clave, huella, Jsonb(resultado)),
            )
