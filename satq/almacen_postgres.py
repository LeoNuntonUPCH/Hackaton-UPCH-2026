from __future__ import annotations

import os
from pathlib import Path

from .datos import Alerta, CambioParametro, Comunicacion, Quebrada, Suscriptor
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
        for ruta in sorted(RUTA_SQL.parent.glob("*.sql")):
            cur.execute(ruta.read_text(encoding="utf-8"))
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
                    "entrega_real, proveedor, id_externo, error, intentos, "
                    "destino, clave_idempotencia FROM comunicaciones "
                    "ORDER BY momento DESC")
        repo._comunicaciones = [Comunicacion(
            momento=r[0], quebrada=r[1], destinatarios=r[2], canal=r[3],
            resultado=r[4], entrega_real=r[5], proveedor=r[6],
            id_externo=r[7], error=r[8], intentos=r[9], destino=r[10],
            clave_idempotencia=r[11],
        ) for r in cur.fetchall()]
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
        cur.execute("SELECT telefono, canal, quebrada, nombre, lat, lon, "
                    "consentimiento, activo, creado, origen, telegram_chat_id, "
                    "telegram_usuario, verificado, codigo_hash, codigo_expira, "
                    "intentos_codigo FROM suscriptores")
        repo._suscriptores = {
            f"{r[1]}:{r[0]}": Suscriptor(
                telefono=r[0], canal=r[1], quebrada=r[2], nombre=r[3],
                lat=r[4], lon=r[5], consentimiento=r[6], activo=r[7],
                creado=r[8], origen=r[9], telegram_chat_id=r[10],
                telegram_usuario=r[11], verificado=r[12], codigo_hash=r[13],
                codigo_expira=r[14], intentos_codigo=r[15],
            )
            for r in cur.fetchall()
        }


def guardar(estado) -> None:
    from psycopg.types.json import Jsonb
    with _conectar() as cx, cx.cursor() as cur:
        cur.execute("TRUNCATE quebradas, alertas, comunicaciones, "
                    "historial_parametros, umbrales, ingestas, alertas_clave, "
                    "suscriptores")
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
                "canal, resultado, entrega_real, proveedor, id_externo, error, "
                "intentos, destino, clave_idempotencia) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (c.momento, c.quebrada, c.destinatarios, c.canal,
                 c.resultado, c.entrega_real, c.proveedor, c.id_externo,
                 c.error, c.intentos, c.destino, c.clave_idempotencia),
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
        for s in repo._suscriptores.values():
            cur.execute(
                "INSERT INTO suscriptores (telefono, canal, quebrada, nombre, "
                "lat, lon, consentimiento, activo, creado, origen, "
                "telegram_chat_id, telegram_usuario, verificado, codigo_hash, "
                "codigo_expira, intentos_codigo) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (s.telefono, s.canal, s.quebrada, s.nombre, s.lat, s.lon,
                 s.consentimiento, s.activo, s.creado, s.origen,
                 s.telegram_chat_id, s.telegram_usuario, s.verificado,
                 s.codigo_hash, s.codigo_expira, s.intentos_codigo),
            )
