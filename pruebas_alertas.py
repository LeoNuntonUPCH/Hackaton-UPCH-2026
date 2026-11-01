"""Pruebas del endpoint POST /api/alertas.

Ejecutar desde la raíz del repo:

    python -m unittest pruebas_alertas -v
"""

from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

import app as satq_app
from satq.estado import ESTADO

CLAVE = "clave-prueba"


class PruebasAlertas(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SATQ_INGESTA_API_KEY"] = CLAVE
        ESTADO.reiniciar()
        self.client = TestClient(satq_app.app)

    def payload(self, **cambios) -> dict:
        datos = {
            "quebrada": "quirio",
            "fuente": "pruebas",
            "idempotency_key": "alerta-1",
        }
        datos.update(cambios)
        return datos

    def post(self, payload: dict, headers: dict | None = None):
        return self.client.post(
            "/api/alertas",
            json=payload,
            headers=headers if headers is not None else {"X-API-Key": CLAVE},
        )

    def elevar_quirio(self) -> None:
        ESTADO.ingerir_lecturas(
            "quirio", [100.0], "pruebas", "ingesta-quirio"
        )

    def test_sin_clave_devuelve_401(self) -> None:
        respuesta = self.post(self.payload(), headers={})
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

    def test_nivel_bajo_no_crea_alerta(self) -> None:
        respuesta = self.post(self.payload())
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("no requiere alerta", respuesta.json()["detail"])

    def test_crea_alerta_con_codigo_consecutivo(self) -> None:
        self.elevar_quirio()
        respuesta = self.post(self.payload())
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertTrue(datos["creada"])
        self.assertFalse(datos["duplicado"])
        self.assertEqual(datos["alerta"]["codigo"], "AL-0008")
        self.assertEqual(datos["alerta"]["quebrada"], "quirio")
        self.assertEqual(datos["alerta"]["estado"], "pendiente")
        self.assertEqual(datos["alerta"]["nivel"], "critico")

    def test_reintento_idempotente_no_duplica(self) -> None:
        self.elevar_quirio()
        primera = self.post(self.payload())
        self.assertEqual(primera.status_code, 201)
        antes = len(ESTADO.alertas)
        codigo = primera.json()["alerta"]["codigo"]

        segunda = self.post(self.payload())
        self.assertEqual(segunda.status_code, 200)
        self.assertTrue(segunda.json()["duplicado"])
        self.assertEqual(segunda.json()["alerta"]["codigo"], codigo)
        self.assertEqual(len(ESTADO.alertas), antes)

    def test_misma_clave_con_otra_fuente_devuelve_409(self) -> None:
        self.elevar_quirio()
        self.assertEqual(self.post(self.payload()).status_code, 201)
        respuesta = self.post(self.payload(fuente="otra-fuente"))
        self.assertEqual(respuesta.status_code, 409)

    def test_no_duplica_alerta_activa_de_huaycoloro(self) -> None:
        respuesta = self.post(
            self.payload(
                quebrada="huaycoloro",
                idempotency_key="alerta-huaycoloro",
            )
        )
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertFalse(datos["creada"])
        self.assertEqual(datos["motivo"], "alerta_activa")
        self.assertEqual(datos["alerta"]["codigo"], "AL-0007")


if __name__ == "__main__":
    unittest.main()
