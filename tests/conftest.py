"""Configuración compartida de las pruebas.

Fuerza el modo memoria para que las pruebas nunca toquen PostgreSQL y ofrece
un ``Estado`` aislado por test.
"""

from __future__ import annotations

import os

# Debe ejecutarse antes de importar satq.estado (crea el singleton ESTADO).
os.environ.pop("SATQ_DB", None)
os.environ.pop("SATQ_DSN", None)

import pytest  # noqa: E402

from satq.estado import Estado  # noqa: E402
from satq.repositorio_memoria import RepositorioMemoria  # noqa: E402


@pytest.fixture(autouse=True)
def _sin_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SATQ_DB", raising=False)
    monkeypatch.delenv("SATQ_DSN", raising=False)


@pytest.fixture
def estado() -> Estado:
    return Estado(RepositorioMemoria())
