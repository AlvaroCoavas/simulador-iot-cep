"""Punto de entrada de la app Android (lo que ejecuta buildozer).

En el escritorio se puede lanzar con:
    py -3.14 -m movil.main

En Android, buildozer exige que el script principal se llame `main.py` en la
raiz del proyecto, asi que este archivo solo delega en `movil.main`.
"""

from __future__ import annotations

from movil.main import main

if __name__ == "__main__":
    raise SystemExit(main())
