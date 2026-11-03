"""Arranque de Satqito: `python -m satqito`."""

from __future__ import annotations

import os

from .api import ApiSatq
from .bot import Satqito
from .telegram import Telegram


def main() -> int:
    token = os.environ.get("SATQ_TELEGRAM_BOT_TOKEN", "").strip()
    clave = os.environ.get("SATQ_BOT_API_KEY", "").strip()
    base = os.environ.get("SATQ_API_URL", "http://127.0.0.1:8000").strip()
    if not token or not clave:
        print(
            "Faltan variables de entorno:\n"
            "  SATQ_TELEGRAM_BOT_TOKEN\n"
            "  SATQ_BOT_API_KEY\n"
            "  (opcional) SATQ_API_URL"
        )
        return 1
    print(f"Satqito iniciado contra {base}. Ctrl+C para detener.")
    try:
        Satqito(ApiSatq(base, clave), Telegram(token)).run()
    except KeyboardInterrupt:
        print("\nSatqito detenido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
