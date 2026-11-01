"""Pruebas del endpoint POST /api/ingesta.

Ejecutar desde la raíz del repo:

    python -m unittest pruebas_ingesta -v
"""

from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

import app as satq_app
from satq.estado import ESTADO

CLAVE = "clave-prueba"


class PruebasIngesta(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SATQ_INGESTA_API_KEY"] = CLAVE
        ESTADO.reiniciar()
        self.client = TestClient(satq_app.app)

    def payload(self, **cambios) -> dict:
        datos = {
            "quebrada": "huaycoloro",
            "fuente": "pruebas",
            "idempotency_key": "clave-1",
            "lecturas": [{"mm_h": 100.0}],
        }
        datos.update(cambios)
        return datos

    def post(self, payload: dict, headers: dict | None = None):
        return self.client.post(
            "/api/ingesta",
            json=payload,
            headers=headers if headers is not None else {"X-API-Key": CLAVE},
        )

    def test_sin_clave_devuelve_401(self) -> None:
        respuesta = self.post(self.payload(), headers={})
        self.assertEqual(respuesta.status_code, 401)

    def test_clave_incorrecta_devuelve_401(self) -> None:
        respuesta = self.post(
            self.payload(), headers={"X-API-Key": "incorrecta"}
        )
        self.assertEqual(respuesta.status_code, 401)

    def test_sin_clave_configurada_devuelve_503(self) -> None:
        os.environ.pop("SATQ_INGESTA_API_KEY", None)
        try:
            respuesta = self.post(self.payload())
        finally:
            os.environ["SATQ_INGESTA_API_KEY"] = CLAVE
        self.assertEqual(respuesta.status_code, 503)

    def test_quebrada_inexistente_devuelve_404(self) -> None:
        respuesta = self.post(self.payload(quebrada="no-existe"))
        self.assertEqual(respuesta.status_code, 404)

    def test_lectura_invalida_devuelve_400(self) -> None:
        respuesta = self.post(
            self.payload(lecturas=[{"mm_h": -1}])
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_ingesta_valida_actualiza_lecturas(self) -> None:
        antes = len(ESTADO.quebrada("huaycoloro").lecturas)
        respuesta = self.post(self.payload())
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos["quebrada"], "huaycoloro")
        self.assertEqual(datos["idempotency_key"], "clave-1")
        self.assertEqual(datos["nivel"], "critico")
        self.assertTrue(datos["alerta_requerida"])
        self.assertFalse(datos["duplicado"])
        self.assertEqual(datos["lecturas_recibidas"], 1)
        self.assertEqual(
            len(ESTADO.quebrada("huaycoloro").lecturas), antes + 1
        )

    def test_reintento_idempotente_no_duplica(self) -> None:
        primera = self.post(self.payload())
        self.assertEqual(primera.status_code, 200)
        antes = len(ESTADO.quebrada("huaycoloro").lecturas)

        segunda = self.post(self.payload())
        self.assertEqual(segunda.status_code, 200)
        self.assertTrue(segunda.json()["duplicado"])
        self.assertEqual(
            len(ESTADO.quebrada("huaycoloro").lecturas), antes
        )

    def test_misma_clave_con_otro_payload_devuelve_409(self) -> None:
        self.assertEqual(self.post(self.payload()).status_code, 200)
        respuesta = self.post(
            self.payload(lecturas=[{"mm_h": 1.0}])
        )
        self.assertEqual(respuesta.status_code, 409)

    def test_varias_lecturas(self) -> None:
        respuesta = self.post(
            self.payload(lecturas=[{"mm_h": 10.0}, {"mm_h": 20.0}])
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["lecturas_recibidas"], 2)


if __name__ == "__main__":
    unittest.main()
