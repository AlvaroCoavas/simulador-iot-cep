"""Punto de entrada del panel de monitoreo IoT & CEP.

Uso:
    py -m app.main
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from . import theme
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Simulador IoT & CEP")
    app.setStyleSheet(theme.QSS)

    ventana = MainWindow()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
