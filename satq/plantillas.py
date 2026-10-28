"""Entorno Jinja2 compartido por los dos servidores."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

RAIZ = Path(__file__).resolve().parent
DIR_PLANTILLAS = RAIZ / "templates"
DIR_ESTATICOS = RAIZ / "static"

entorno = Environment(
    loader=FileSystemLoader(str(DIR_PLANTILLAS)),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render(nombre: str, contexto: dict) -> str:
    return entorno.get_template(nombre).render(**contexto)
