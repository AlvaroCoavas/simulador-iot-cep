"""Punto de entrada del simulador.

Uso directo:      py simulador.py
Empaquetado:     py -m PyInstaller ... simulador.py

Este archivo existe para que PyInstaller funcione: `app/main.py` usa
imports relativos y solo puede ejecutarse como modulo (`py -m app.main`).
"""

import sys

from app.main import main

if __name__ == "__main__":
    sys.exit(main())
